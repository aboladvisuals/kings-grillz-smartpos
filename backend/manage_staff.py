"""Local administration. Passwords are read only through a hidden prompt."""
import argparse
import getpass

from sqlalchemy import select

from app.database import SessionLocal, engine
from app.security import Staff, ROLES, audit, hash_password, initialize_security, revoke_staff_sessions, username_key


def change_staff(db, action, username, role=None, password=None):
    username = username_key(username)
    if role is not None and role not in ROLES:
        raise ValueError("Unknown staff role")
    staff = db.scalar(select(Staff).where(Staff.username == username))
    if action == "create":
        if staff:
            raise ValueError("Username already exists")
        admins = db.scalars(select(Staff).where(Staff.role == "admin", Staff.active.is_(True))).all()
        if not admins and role != "admin":
            raise ValueError("Create an administrator first")
        staff = Staff(username=username, password_hash=hash_password(password), role=role, active=True)
        db.add(staff)
        db.flush()
    else:
        if staff is None:
            raise ValueError("Staff account not found")
        if staff.active and staff.role == "admin" and (action == "disable" or (action == "set-role" and role != "admin")):
            others = db.scalar(select(Staff.id).where(Staff.role == "admin", Staff.active.is_(True), Staff.id != staff.id))
            if others is None:
                raise ValueError("Cannot disable or demote the last active administrator")
        if action == "disable":
            staff.active = False
        elif action == "enable":
            staff.active = True
        elif action == "set-role":
            staff.role = role
        elif action == "reset-password":
            staff.password_hash = hash_password(password)
        elif action != "revoke-sessions":
            raise ValueError("Unknown action")
        revoke_staff_sessions(db, staff.id)
    audit(db, staff.id, "local_admin_" + action)
    db.commit()


def main():
    parser = argparse.ArgumentParser(description="KING'S GRILLZ local staff administration")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("init", help="Create security tables without modifying existing business records")
    sub.add_parser("list")
    for action in ("create", "disable", "enable", "set-role", "reset-password", "revoke-sessions"):
        command = sub.add_parser(action)
        command.add_argument("username")
        if action in {"create", "set-role"}:
            command.add_argument("--role", choices=sorted(ROLES), required=True)
    args = parser.parse_args()
    initialize_security(engine)
    if args.action == "init":
        print("Security tables initialized. No staff credentials were created.")
        return
    with SessionLocal() as db:
        if args.action == "list":
            for staff in db.scalars(select(Staff).order_by(Staff.username)):
                print(f"{staff.username}\t{staff.role}\t{'active' if staff.active else 'disabled'}")
            return
        password = None
        if args.action in {"create", "reset-password"}:
            password = getpass.getpass("New unique passphrase (15–128 characters): ")
            if password != getpass.getpass("Repeat passphrase: "):
                parser.error("Passphrases do not match")
        try:
            change_staff(db, args.action, args.username, getattr(args, "role", None), password)
        except ValueError as exc:
            db.rollback()
            parser.error(str(exc))
    print("Staff account updated. No credentials were printed.")


if __name__ == "__main__":
    main()

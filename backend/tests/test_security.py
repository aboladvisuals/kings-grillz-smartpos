import asyncio
from http.cookies import SimpleCookie
import json
import os
import secrets
import time
from unittest.mock import patch

from sqlalchemy import func, select

from app.main import app
from app.models.order import Order
from app.models.payment import Payment
from app.security import AuditEvent, Staff, StaffSession, settings, token_hash, verify_password
from manage_staff import change_staff
from test_order_status import SupportCase, request


class SecurityTests(SupportCase):
    def raw(self, method, path, payload=None, headers=None, scheme="http"):
        return asyncio.run(request(method, path, payload, headers, True, scheme))

    def login(self, username="cashier", password=None, headers=None):
        status, body, response_headers = self.raw("POST", "/api/auth/login", {
            "username": username, "password": password or self.password,
        }, {"origin": "http://localhost:5173", **(headers or {})})
        return status, json.loads(body), response_headers

    def logged_in_headers(self, username="cashier"):
        status, body, response_headers = self.login(username)
        self.assertEqual(status, 200)
        cookie = SimpleCookie()
        cookie.load(response_headers["set-cookie"])
        return {"cookie": "kg_session=" + cookie["kg_session"].value,
                "origin": "http://localhost:5173", "x-csrf-token": body["csrf_token"]}

    def test_every_application_route_is_protected_by_default(self):
        public = {("GET", "/health"), ("POST", "/api/auth/login")}
        checked = 0
        for route in app.routes:
            for method in getattr(route, "methods", []):
                if (method, route.path) in public:
                    continue
                path = route.path.replace("{order_id}", "1").replace("{product_id}", "1").replace("{payment_id}", "1")
                with self.subTest(method=method, path=path):
                    status, _, _ = self.raw(method, path, {} if method in {"POST", "PATCH"} else None)
                    self.assertEqual(status, 401)
                    checked += 1
        self.assertGreaterEqual(checked, 13)
        self.assertEqual(self.raw("GET", "/health")[0], 200)
        self.assertEqual(self.raw("GET", "/docs")[0], 404)

    def test_login_cookie_and_password_storage(self):
        status, body, headers = self.login()
        self.assertEqual(status, 200)
        self.assertEqual(body["staff"]["role"], "cashier")
        self.assertTrue(body["staff"]["can_record_payments"])
        self.assertIn("HttpOnly", headers["set-cookie"])
        self.assertIn("SameSite=strict", headers["set-cookie"])
        self.assertIn("Path=/", headers["set-cookie"])
        self.assertNotIn(self.password, json.dumps(body))
        self.assertNotIn("password_hash", json.dumps(body))
        self.assertTrue(self.password_hash.startswith("scrypt$131072$8$1$"))
        self.assertTrue(verify_password(self.password, self.password_hash))
        self.assertFalse(verify_password(secrets.token_urlsafe(24), self.password_hash))
        cookie = SimpleCookie(headers["set-cookie"])
        token = cookie["kg_session"].value
        self.assertIsNone(self.db.get(StaffSession, token))
        self.assertIsNotNone(self.db.get(StaffSession, token_hash(token)))

    def test_unknown_disabled_and_incorrect_credentials_have_generic_error(self):
        status, wrong, _ = self.login(password=secrets.token_urlsafe(24))
        self.assertEqual(status, 401)
        status, unknown, _ = self.login(username="unknown")
        self.assertEqual(status, 401)
        self.db.get(Staff, 2).active = False
        self.db.commit()
        status, disabled, _ = self.login()
        self.assertEqual(status, 401)
        self.assertEqual(wrong, unknown)
        self.assertEqual(wrong, disabled)

    def test_login_origin_and_input_redaction(self):
        for origin in ("https://evil.example", "null", ""):
            self.assertEqual(self.login(headers={"origin": origin})[0], 403)
        marker = secrets.token_urlsafe(30)
        for payload in ({"username": "cashier", "password": marker * 10},
                        {"username": "cashier", "password": marker, "role": "admin"}):
            status, body, _ = self.raw("POST", "/api/auth/login", payload, {"origin": "http://localhost:5173"})
            self.assertEqual(status, 422)
            self.assertNotIn(marker.encode(), body)

    def test_account_and_ip_rate_limits(self):
        # Rate limiting is database-backed and does not trust spoofed forwarding headers.
        for _ in range(5):
            self.assertEqual(self.login(password=secrets.token_urlsafe(24))[0], 401)
        self.assertEqual(self.login()[0], 429)
        with patch("app.auth.verify_password", return_value=False):
            statuses = [self.login(username=f"unknown{i}", headers={"x-forwarded-for": f"10.0.0.{i}"})[0] for i in range(31)]
        self.assertIn(429, statuses)
        self.assertEqual(statuses[-1], 429)

    def test_forged_missing_and_expired_sessions(self):
        for headers in ({}, {"authorization": "Bearer forged", "x-role": "admin"}, {"cookie": "kg_session=" + secrets.token_urlsafe(32)}):
            self.assertEqual(self.raw("GET", "/api/orders", headers=headers)[0], 401)
        for field, value in (("expires_at", int(time.time()) - 1), ("last_seen", int(time.time()) - 1801)):
            headers = self.session_headers(2)
            session = self.db.get(StaffSession, token_hash(headers["cookie"].split("=", 1)[1]))
            setattr(session, field, value)
            self.db.commit()
            self.assertEqual(self.raw("GET", "/api/orders", headers=headers)[0], 401)

    def test_csrf_required_for_all_business_mutations_and_logout(self):
        order_id = self.order()
        endpoints = [("POST", "/api/orders", {}), ("POST", f"/api/orders/{order_id}/payments", {"amount": 1, "method": "Cash", "reference": "csrf"}),
                     ("PATCH", f"/api/orders/{order_id}/status", {"order_status": "preparing"}), ("POST", "/api/auth/logout", {})]
        for method, path, payload in endpoints:
            for change in ({"x-csrf-token": ""}, {"x-csrf-token": "forged"}, {"x-csrf-token": "é"}, {"origin": "https://evil.example"}, {"origin": ""}):
                with self.subTest(method=method, path=path, change=change):
                    self.assertEqual(self.raw(method, path, payload, {**self.headers, **change})[0], 403)
        self.db.expire_all()
        self.assertEqual(self.db.get(Order, order_id).order_status, "pending")
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Payment)), 0)

    def test_operations_can_fulfil_but_cannot_record_payments(self):
        order_id = self.order()
        headers = self.logged_in_headers("operations")
        payload = {"amount": 100, "method": "Cash", "reference": "unauthorized"}
        self.assertEqual(self.raw("POST", f"/api/orders/{order_id}/payments", payload, {**headers, "x-role": "admin"})[0], 403)
        self.assertEqual(self.raw("PATCH", f"/api/orders/{order_id}/status", {"order_status": "preparing"}, headers)[0], 200)
        self.assertEqual(self.raw("GET", f"/api/orders/{order_id}/invoice", headers=headers)[0], 200)
        self.assertEqual(self.raw("GET", "/openapi.json", headers=headers)[0], 403)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Payment)), 0)

    def test_cashier_payment_has_audit_attribution_and_protected_receipt(self):
        order_id = self.order()
        headers = self.logged_in_headers()
        payload = {"amount": 4000, "method": "Cash", "reference": "authorized-payment"}
        status, body, _ = self.raw("POST", f"/api/orders/{order_id}/payments", payload, headers)
        self.assertEqual(status, 201)
        payment_id = json.loads(body)["payment_id"]
        event = self.db.scalar(select(AuditEvent).where(AuditEvent.action == "payment_recorded"))
        self.assertEqual((event.staff_id, event.resource_id), (2, payment_id))
        path = f"/api/payments/{payment_id}/receipt"
        self.assertEqual(self.raw("GET", path)[0], 401)
        status, pdf, response_headers = self.raw("GET", path, headers=headers)
        self.assertEqual(status, 200)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertEqual(response_headers["cache-control"], "no-store")
        self.assertEqual(self.raw("POST", f"/api/orders/{order_id}/payments", payload, headers)[0], 409)
        self.db.expire_all()
        self.assertEqual(self.db.get(Order, order_id).amount_paid, 4000)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Payment)), 1)
        self.assertEqual(self.raw("POST", f"/api/orders/{order_id}/payments", {**payload, "amount": 7000, "reference": "overpay"}, headers)[0], 400)

    def test_logout_and_login_rotation_revoke_tokens(self):
        first = self.logged_in_headers()
        status, body, headers = self.login(headers={"cookie": first["cookie"]})
        self.assertEqual(status, 200)
        self.assertEqual(self.raw("GET", "/api/auth/me", headers=first)[0], 401)
        cookie = SimpleCookie(headers["set-cookie"])
        current = {"cookie": "kg_session=" + cookie["kg_session"].value, "origin": "http://localhost:5173", "x-csrf-token": body["csrf_token"]}
        self.assertEqual(self.raw("POST", "/api/auth/logout", {}, current)[0], 204)
        self.assertEqual(self.raw("GET", "/api/orders", headers=current)[0], 401)

    def test_local_admin_changes_revoke_sessions_and_protect_last_admin(self):
        for action, kwargs in (("set-role", {"role": "operations"}), ("reset-password", {"password": secrets.token_urlsafe(24)}), ("disable", {})):
            headers = self.session_headers(2)
            change_staff(self.db, action, "cashier", **kwargs)
            self.assertEqual(self.raw("GET", "/api/orders", headers=headers)[0], 401)
        with self.assertRaises(ValueError):
            change_staff(self.db, "disable", "admin")
        with self.assertRaises(ValueError):
            change_staff(self.db, "set-role", "admin", role="cashier")

    def test_security_headers_host_validation_and_body_limit(self):
        status, _, headers = self.raw("GET", "/api/orders")
        self.assertEqual(status, 401)
        for key in ("cache-control", "x-content-type-options", "content-security-policy", "referrer-policy", "x-frame-options"):
            self.assertIn(key, headers)
        self.assertEqual(self.raw("GET", "/health", headers={"host": "evil.example"})[0], 400)
        self.assertEqual(self.raw("POST", "/api/auth/login", {}, {"content-type": "text/plain"})[0], 415)
        self.assertEqual(self.raw("POST", "/api/auth/login", {"data": "x" * 17000})[0], 413)
        self.assertNotIn("access-control-allow-origin", self.raw("GET", "/api/orders", headers={"origin": "https://evil.example"})[2])

    def test_production_fails_closed_and_sets_secure_cookie(self):
        try:
            for origin in ("", "http://example.com", "https://*.example.com", "https://example.com/path"):
                with patch.dict(os.environ, {"KG_ENV": "production", "KG_ALLOWED_ORIGINS": origin}):
                    settings.cache_clear()
                    with self.assertRaises(RuntimeError): settings()
            with patch.dict(os.environ, {
    "KG_ENV": "production",
    "KG_ALLOWED_ORIGINS": "https://localhost",
    "KG_ALLOWED_HOSTS": "localhost",
}):
                settings.cache_clear()
                self.assertEqual(self.raw("GET", "/health")[0], 200)
                self.assertEqual(self.raw("GET", "/api/orders")[0], 400)
                status, _, headers = self.raw("POST", "/api/auth/login", {"username": "cashier", "password": self.password}, {"origin": "https://localhost"}, "https")
                self.assertEqual(status, 200)
                self.assertIn("__Host-kg_session=", headers["set-cookie"])
                self.assertIn("Secure", headers["set-cookie"])
                self.assertIn("HttpOnly", headers["set-cookie"])
                self.assertIn("strict-transport-security", headers)
        finally:
            settings.cache_clear()

    def test_password_work_is_bounded_and_role_change_is_immediate(self):
        from app.auth import password_slots
        password_slots.acquire()
        password_slots.acquire()
        try:
            self.assertEqual(self.login()[0], 429)
        finally:
            password_slots.release()
            password_slots.release()
        headers = self.session_headers(2)
        order_id = self.order()
        self.db.get(Staff, 2).role = "operations"
        self.db.commit()
        status, _, _ = self.raw("POST", f"/api/orders/{order_id}/payments", {"amount": 1, "method": "Cash", "reference": "role-changed"}, headers)
        self.assertEqual(status, 403)

    def test_malformed_money_and_injected_fields_are_rejected(self):
        order_id = self.order()
        for amount in (-1, 0, 1.5, True, "100", 10**30):
            self.assertEqual(self.raw("POST", f"/api/orders/{order_id}/payments", {"amount": amount, "method": "Cash", "reference": "invalid"}, self.headers)[0], 422)
        self.assertEqual(self.raw("POST", f"/api/orders/{order_id}/payments", {"amount": 1, "method": "Cash", "reference": "invalid", "staff_id": 99}, self.headers)[0], 422)
        self.assertEqual(self.raw("PATCH", f"/api/orders/{order_id}/status", {"order_status": "preparing", "amount_paid": 999}, self.headers)[0], 422)
        payload = {"customer_name": "Test", "customer_phone": "08012345678", "quantity": 1, "preparation": "Whole", "fulfilment": "Delivery", "delivery_provider": "Company Rider", "delivery_address": "a" * 256}
        self.assertEqual(self.raw("POST", "/api/orders", payload, self.headers)[0], 422)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Payment)), 0)

    def test_concurrent_payments_cannot_overpay(self):
        from concurrent.futures import ThreadPoolExecutor
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from threading import Barrier
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from app.database import Base, get_db
        from app.models.customer import Customer
        from app.models.product import Product

        previous_override = app.dependency_overrides[get_db]
        with TemporaryDirectory() as directory:
            engine = create_engine('sqlite:///' + str(Path(directory) / 'concurrent.db'), connect_args={"check_same_thread": False, "timeout": 15})
            Base.metadata.create_all(engine)
            token = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(32)
            now = int(time.time())
            with Session(engine) as db:
                db.add_all([
                    Staff(id=1, username="cashier", password_hash=self.password_hash, role="cashier", active=True),
                    Customer(id=1, name="Test", phone="08012345678"),
                    Product(id=1, name="Test", price=100, available=True),
                ])
                db.commit()
                db.add(Order(id=1, order_number="CONCURRENT", customer_id=1, product_id=1, quantity=1,
                             unit_price=100, preparation="Whole", fulfilment="Pickup", subtotal=100, total=100,
                             amount_paid=0, payment_status="unpaid", order_status="pending"))
                db.add(StaffSession(token_hash=token_hash(token), staff_id=1, csrf_token=csrf, expires_at=now+3600, last_seen=now))
                db.commit()
            def isolated_db():
                with Session(engine) as db:
                    yield db
            app.dependency_overrides[get_db] = isolated_db
            barrier = Barrier(2)
            def pay(index):
                barrier.wait(timeout=10)
                return self.raw("POST", "/api/orders/1/payments", {"amount": 70, "method": "Cash", "reference": f"concurrent-{index}"},
                                {"cookie": "kg_session=" + token, "x-csrf-token": csrf, "origin": "http://localhost:5173"})[0]
            try:
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(pay, [1, 2]))
                self.assertEqual(results.count(201), 1)
                self.assertTrue(any(code in {400, 409} for code in results))
                with Session(engine) as db:
                    self.assertEqual(db.get(Order, 1).amount_paid, 70)
                    self.assertEqual(db.scalar(select(func.sum(Payment.amount))), 70)
                    self.assertEqual(db.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.action == "payment_recorded")), 1)
            finally:
                app.dependency_overrides[get_db] = previous_override
                engine.dispose()

    def test_session_revoked_during_authentication_fails_closed(self):
        from sqlalchemy import delete
        from sqlalchemy.sql.dml import Update
        execute = self.db.execute
        revoked = False
        def revoke_before_touch(statement, *args, **kwargs):
            nonlocal revoked
            if not revoked and isinstance(statement, Update) and statement.table.name == 'staff_sessions':
                revoked = True
                execute(delete(StaffSession))
            return execute(statement, *args, **kwargs)
        with patch.object(self.db, 'execute', side_effect=revoke_before_touch):
            self.assertEqual(self.raw('GET', '/api/orders', headers=self.headers)[0], 401)

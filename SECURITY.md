# Historical SmartPOS security notes

This file describes the archived cloud SmartPOS staff-login system.
Receipt Studio is the active product and does not use login, cookies, or a remote API.
See the repository README and `archive/smartpos-cloud-2026-10-17`.

---

# KING'S GRILLZ staff security

Status: implemented locally; public deployment is not authorized or approved.

## Access policy

All application routes require an active staff session by default, except `GET /health` and `POST /api/auth/login`. Public registration does not exist. Interactive API documentation is disabled; the schema endpoint requires an administrator.

| Capability | Operations | Cashier | Admin |
| --- | --- | --- | --- |
| Read products, orders, customer details and financial summaries | Yes | Yes | Yes |
| Create orders and update fulfilment | Yes | Yes | Yes |
| Read payment history, download invoices/receipts, prepare WhatsApp links | Yes | Yes | Yes |
| Record payments | No | Yes | Yes |
| Read API schema | No | No | Yes |

This is a single-business staff policy. There is no tenant separation or per-order ownership rule. All authenticated staff can read customer and financial information. Account administration is available only through the local command below, under the operating-system administrator's control; an API role does not grant shell access.

## Local setup and account administration

Run these commands from `C:\Users\abola\Documents\kings-grillz\backend`:

```powershell
.\.venv\Scripts\python.exe manage_staff.py init
.\.venv\Scripts\python.exe manage_staff.py create owner --role admin
.\.venv\Scripts\python.exe manage_staff.py create staff-name --role cashier
.\.venv\Scripts\python.exe manage_staff.py create kitchen-name --role operations
```

Create the administrator first. Passwords are entered at a hidden interactive prompt, never as command arguments or in source files. Use a unique passphrase of 15–128 characters. No real account or default credential is created by installation. The initialization adds security tables without rewriting business tables.

```powershell
.\.venv\Scripts\python.exe manage_staff.py list
.\.venv\Scripts\python.exe manage_staff.py reset-password staff-name
.\.venv\Scripts\python.exe manage_staff.py disable staff-name
.\.venv\Scripts\python.exe manage_staff.py enable staff-name
.\.venv\Scripts\python.exe manage_staff.py set-role staff-name --role operations
.\.venv\Scripts\python.exe manage_staff.py revoke-sessions staff-name
```

Administrative changes revoke that staff member's sessions. The final active administrator cannot be disabled or demoted. Recovery and administration require trusted local OS access. Protect the project, database, backups and command access with appropriate filesystem permissions; do not share staff accounts.

Start the backend on loopback:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

In the frontend directory, run `npm run dev` and use `http://localhost:5173`. Restart an existing Vite process after this update so it loads the new proxy configuration. `/api` requests and PDF downloads use the same origin. Do not serve the frontend with a file URL or an unconfigured preview server. The local cookie is intentionally HTTP-compatible only for loopback development.

## Implemented controls

- Password hashing: scrypt N=131072, r=8, p=1, with random 16-byte salts. No reversible password storage. At most two password-verification operations run concurrently per worker to bound memory consumption.
- Sessions: random 256-bit opaque identifiers, only SHA-256 identifier hashes stored in the database. HttpOnly, SameSite=Strict cookies; production uses Secure and the `__Host-` prefix. Absolute expiry is eight hours; idle expiry is thirty minutes, enforced by the server. Reauthentication rotates the session; logout deletes it. Account status and role are checked from the database on each request. No bearer token or session identifier is stored in browser storage or URLs.
- CSRF: exact configured Origin checks and a per-session synchronizer token on every authenticated mutation. Login also checks Origin. CSRF tokens are held only in frontend memory and recovered through authenticated `/api/auth/me` after reload.
- Brute-force controls: database-backed fixed fifteen-minute counters; five failed account attempts and thirty source-IP attempts allowed before blocking. Successful login clears the account counter, not the IP counter. Forwarded headers are not read by application code; proxy trust must be configured explicitly at deployment.
- Payment authorization and integrity: cashier/admin only; atomic conditional balance updates prevent concurrent overpayment. Duplicate references remain unique, with rollback. Payment audit events identify the staff member and payment in the same database transaction. Order creation and fulfilment mutations also record staff attribution. Status updates compare the existing status before committing.
- Input protection: JSON-only writes, 16 KiB body limit, bounded strings and whole-naira amounts, unknown mutation fields rejected. Validation responses omit raw input; SQL error output hides parameters.
- Responses: no-store caching, nosniff, no-referrer, frame denial, restrictive API CSP, and production HSTS. Host validation is enabled. Credentialed cross-origin API access is not enabled.
- Secret hygiene: database, environment, key, log, build and dependency directories are ignored by Git. No production credentials are included. Pinned Python package versions are in `backend/requirements.txt`; frontend uses its existing lockfile.

## Deployment blockers and residual risks

1. **No public deployment yet.** Provision real individual staff accounts and review the role policy. No first administrator password has been chosen by the agent.
2. **HTTPS and hosting configuration are not deployed or verified.** Use a single public HTTPS origin with a reverse proxy serving the built frontend and forwarding `/api` to the private backend. Set `KG_ENV=production` and `KG_ALLOWED_ORIGINS` to the exact HTTPS origin(s), without trailing slashes. Production startup rejects missing/insecure/wildcard origins and rejects non-HTTPS requests. Only trust forwarding headers from your actual proxy, never from arbitrary clients. Do not expose the Vite dev server or backend port publicly.
3. **Frontend security headers must be applied by the static host.** The API supplies its own headers. Configure the frontend with `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` for HTML, and HSTS only on the final HTTPS domain. Verify CSP and PDF behavior behind the actual proxy before release.
4. **No MFA or passkeys yet.** Password theft and phishing can still compromise a staff account. Add MFA/SSO, or restrict initial production access through a trusted private network/access gateway.
5. **Local storage and audit limits.** SQLite and audit events are not encrypted or independently tamper-evident. Someone with OS/database write access can alter records. Configure disk encryption, restricted service accounts, protected backups, restore testing, off-host audit retention and monitoring. SQLite is suitable for a modest single-host workload; multi-host production and heavier concurrency require a planned database migration and load testing.
6. **Availability and abuse limits.** Application login throttling is not a substitute for proxy request/body/time limits, bot protection and monitoring. Distributed attackers can cause account lockouts or consume resources; authenticated staff can request expensive PDFs. Tune proxy limits and monitor capacity. Avoid exposing unauthenticated development tooling.
7. **Payment verification remains manual.** Authorization and audit attribution prove which staff account recorded a payment; they do not verify bank settlement. Staff must independently verify funds. No refund, reconciliation or tamper-evident financial ledger has been added.
8. **Security testing is bounded.** Automated tests and dependency advisory scans are not a penetration test or proof of absence of vulnerabilities. Validate the deployed TLS/proxy/cookie/CSP configuration, recovery process, browser behavior, backup policy, and dependency provenance before approval. Pinning versions alone does not provide signed artifacts or hash-verified installs.

## Repeatable checks

From `frontend`:

```powershell
npm run lint
npm run build
node --test tests/*.test.mjs
npm audit
```

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use isolated databases and generated disposable credentials. They do not mutate production orders or use real staff passwords. The final Step 18 verification report records exact results and any incomplete advisory coverage.

## References

The password and session design follows [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), and [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html). SameSite is used alongside CSRF validation, rather than as a replacement.

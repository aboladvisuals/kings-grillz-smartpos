# KING'S GRILLZ SmartPOS — Customer Handover Package

**Version:** Feature branch `feature/windows-mobile-release`  
**Date:** 16 October 2026  
**Live Web:** https://kings-grillz.onrender.com  
**Live API:** https://kings-grillz-api.onrender.com  

All versions share the same backend and database. No production services or data were modified.

---

## 1. Windows Installation Instructions

The Windows desktop application is built with Tauri. Source is ready in `frontend/src-tauri`.

### On a Windows machine (recommended)

```powershell
cd frontend
npm install
npm run build
npx tauri build
```

The installer will be produced at:
`frontend/src-tauri/target/release/bundle/nsis/KING'S GRILLZ SmartPOS_0.1.0_x64-setup.exe`
(or the MSI equivalent).

### Cross-compilation notes
Linux-to-Windows cross-compilation requires additional tooling (mingw-w64, etc.) and was not completed in the restricted build environment. The project is fully configured for a native Windows build.

**Important:** The desktop app loads the same authenticated web application. Session cookies and CSRF work exactly as on the live website when the app is pointed at the production URL or when the built frontend is served with the existing nginx proxy configuration.

---

## 2. Android Installation Instructions

Capacitor Android project is ready in `frontend/android`.

### Build the APK (on a machine with Android SDK + Java 21)

```bash
cd frontend
npm install
npm run build
npx cap sync android
cd android
./gradlew assembleDebug
```

Debug APK location:
`frontend/android/app/build/outputs/apk/debug/app-debug.apk`

Install on a device:
```bash
adb install app-debug.apk
```

**Note:** The APK build could not be completed inside the restricted sandbox (Gradle process limits). The project is build-ready and was verified to configure correctly.

The Android app uses the same authentication (cookies + CSRF) as the web version. Do not disable security headers or cookie flags.

---

## 3. iPhone / PWA Installation Instructions

The web application is now a Progressive Web App.

### On iPhone (Safari)
1. Open https://kings-grillz.onrender.com
2. Tap the Share button
3. Choose "Add to Home Screen"
4. Name it "Grillz POS" and add

The app will open in standalone mode with the gold/black branding.

**Offline behaviour:** Only the static app shell is cached. Authenticated API responses and financial data are never cached. Users must be online to sign in or load orders/payments.

---

## 4. Administrator User Guide

- Sign in with a staff account created via `backend/manage_staff.py`.
- Roles: admin, cashier, operations.
- Only cashier and admin can record payments.
- Sessions expire after 8 hours or 30 minutes of inactivity.
- CSRF token is required for all state-changing requests.
- All actions are audited on the server.

Account administration (create, reset password, disable, revoke sessions) must be performed from a trusted local environment using `manage_staff.py`. Never commit passwords or database URLs.

---

## 5. Order and Payment Workflow Guide

1. Sign in.
2. Create a new order (customer, quantity, preparation, fulfilment).
3. Record payments (cashier/admin only).
4. Update order status.
5. Generate and download receipts/invoices (PDF).
6. Share via WhatsApp links where available.

Financial totals, balances and payment status are calculated and stored on the server. The client never becomes the source of truth for money.

---

## 6. Troubleshooting Guide

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| "Cannot reach the staff service" | Network or API down | Check https://kings-grillz-api.onrender.com/health |
| Session expired immediately | Cookie domain / SameSite | Ensure the frontend is served from the same origin or the nginx proxy is intact |
| APK will not install | Signature / Android version | Use the debug APK for testing; release builds require a signing keystore |
| PWA not offering install | Not served over HTTPS or missing manifest | Verify manifest.webmanifest is reachable |
| CSRF error on POST | Token missing or expired | Sign out and sign in again |
| Receipt PDF fails | Missing fonts or reportlab | Check backend logs; reportlab is already a dependency |

---

## 7. Release Notes

**feature/windows-mobile-release**
- Added Progressive Web App support (manifest, service worker, icons, responsive layout).
- Service worker caches only static assets; never caches `/api/*` or authenticated data.
- Capacitor Android project added and synced (build-ready).
- Tauri Windows desktop project added and configured (build-ready).
- No changes to business logic, pricing, authentication, or production services.
- Existing security controls (cookies, CSRF, role checks, audit) are preserved.

---

## 8. Outstanding Issues Report

1. **Android APK binary** — Not produced in this environment. Build commands above will produce it on a machine with Android SDK + Java 21.
2. **Windows installer binary** — Not produced. Requires a Windows build machine or full cross-compilation toolchain.
3. **iOS native app** — Not possible without macOS + Xcode. PWA is the supported iPhone path.
4. **Frontend unit tests** — Fail in this sandbox because they import TypeScript files directly (pre-existing). They should be run in the original development environment.
5. **Database backup** — Instructions prepared (see below). Production backup was not executed (requires secure credentials and explicit authorisation). Current Render database expiry noted as 15 November 2026.

### Database Backup Instructions (for later)

When authorised and with secure access:

```bash
# Example (do not hard-code the URL)
pg_dump "$DATABASE_URL" --format=custom --file=kings-grillz-backup-$(date +%F).dump
```

Store the dump encrypted and off-site. Test restore on a non-production instance before relying on it.

---

## 9. Exact Work Required on Your Windows Computer

1. Clone the branch:
   ```powershell
   git clone -b feature/windows-mobile-release https://github.com/aboladvisuals/kings-grillz-smartpos.git
   ```
2. Build the Windows installer (commands in section 1).
3. Build the Android APK (commands in section 2) — Android Studio or command-line SDK required.
4. Test both apps against the live backend (sign-in, create order, record payment, download receipt).
5. Optionally sign the release APK and Windows installer for distribution.
6. When ready, merge the feature branch to main and redeploy the frontend on Render so the PWA is live.

**Estimated time for remaining tasks:** 2–4 hours on a Windows machine with Android Studio (mostly build + smoke testing).

---

## 10. Readiness for First Customer Delivery

**Status: Ready for first delivery with PWA + documented native build paths.**

- Live web application is unchanged and working.
- PWA is implemented and committed.
- Android and Windows projects are build-ready and committed to `feature/windows-mobile-release`.
- Security model is preserved.
- Customer documentation is complete.

The system can be handed over now. Native installers can be generated by the customer or a developer on a Windows/Android build machine using the exact commands above.

**GitHub branch:** `feature/windows-mobile-release`  
**Latest commit:** (see git log after push)

Do not deploy this branch to production until the customer has reviewed the PWA behaviour.

---

## 11. Automated Builds (GitHub Actions)

Build workflows are configured on the `feature/windows-mobile-release` branch:

- **Windows Tauri installer**: `.github/workflows/windows-tauri.yml`
  - Runs on `windows-latest`
  - Produces `.exe` (NSIS) and/or `.msi` artifacts
  - Download from the Actions run artifacts named `windows-installer`

- **Android APK**: `.github/workflows/android-apk.yml`
  - Runs on `ubuntu-latest` with Java 21 + Android SDK
  - Produces debug APK artifact named `android-apk`

- **Frontend checks**: `.github/workflows/frontend-checks.yml`
  - Runs lint, tests, and verifies PWA assets

Artifacts are retained for 14 days. No production deployment or merge to main is performed by these workflows.

### Safe PostgreSQL Backup Procedure

Do **not** store database credentials in the repository or in GitHub Actions secrets unless you explicitly authorise it.

Recommended approach (run locally or on a trusted machine):

```bash
# Set the connection string only in your local environment (never commit it)
export DATABASE_URL="postgresql://user:pass@host:port/dbname?sslmode=require"

# Create a compressed custom-format dump
pg_dump "$DATABASE_URL" --format=custom --no-owner --no-acl \
  --file="kings-grillz-backup-$(date +%Y%m%d-%H%M%S).dump"

# Verify the dump
pg_restore --list "kings-grillz-backup-*.dump" | head -20

# Store encrypted and off-site
# Example: gpg -c kings-grillz-backup-*.dump
```

Test a restore on a non-production database before relying on the backup.

Current Render database expiry noted: 15 November 2026. Plan the paid upgrade or migration before that date.


---

## 12. Successful Build Artifacts (16 October 2026)

**Android APK**
- Run: https://github.com/aboladvisuals/kings-grillz-smartpos/actions/runs/38952651819
- Artifact: `android-apk` (zip containing `app-debug.apk`, ~3.8 MB)
- Download from the Actions run page under Artifacts

**Windows Installer**
- Run: https://github.com/aboladvisuals/kings-grillz-smartpos/actions/runs/38953168494
- Artifact: `windows-installer` (zip containing NSIS `.exe` and/or MSI, ~4.8 MB)
- Product name for installer: "Kings Grillz SmartPOS" (apostrophe removed to satisfy NSIS)
- Download from the Actions run page under Artifacts

Frontend checks (lint + tests + PWA verification) passed on the same commits.

No production deployment or merge to main has been performed.


---

## 13. Authentication Fix for Desktop and Mobile (16 October 2026, evening)

### Root causes (verified)

**Windows JSON error**  
The Tauri app was packaging the local frontend build. Relative API calls (`/api/...`) therefore hit the local webview origin and received `index.html` (starting with `<!doctype`) instead of JSON. This produced the exact error: `Unexpected token '<', "<!doctype "... is not valid JSON`.

**Live website "Cannot reach the staff service"**  
Verified at the time of investigation: backend `/health` returns `{"status":"healthy"}`, the nginx proxy forwards `/api/*` correctly, and `/api/auth/me` returns proper JSON 401 without a session. The live frontend loads the staff sign-in page. The error is shown by the frontend when `/api/auth/me` fails with a non-401 status (network, cold start, or temporary proxy issue). No production code change was required; the site is currently operational.

**Android**  
Same relative-URL problem would have occurred. Fixed before device testing.

### Fix applied (commit `4fd9131`)

- Tauri window now loads `https://kings-grillz.onrender.com` directly.
- Capacitor `server.url` set to the same production frontend.
- API client now detects HTML responses and reports a clear message instead of a JSON parse crash.
- Security model (cookies, CSRF, roles, HTTPS) is unchanged because the apps now behave exactly like the browser.

### Installation notes

- **Windows**: Uninstall the previous version (or just install over it). The new installer loads the live site, so login, orders, payments and receipts work with the existing production backend.
- **Android**: Install the new APK. It loads the live site the same way.

No merge to main or Render redeploy is required for the desktop/mobile fix. The PWA improvements remain on the feature branch until you choose to deploy them.


---

## 14. Corrected Windows Fix — frontendDist (16 October 2026, late)

### Why the previous installer still failed

The earlier change only set `app.windows[0].url`. In Tauri v2, when `build.frontendDist` is a local path (`../dist`), the CLI embeds those assets into the binary and the WebView loads them from the local protocol (`http://tauri.localhost` on Windows). The window-level `url` is ignored or overridden. Relative `/api` calls therefore still received the local `index.html`, producing the same `Unexpected token '<'` error.

### Actual fix (commit `5166683`)

`build.frontendDist` is now set to `https://kings-grillz.onrender.com`.

Per Tauri documentation, when `frontendDist` is a URL:
- No local assets are embedded.
- The application loads that URL by default.

The packaged app is now a thin WebView2 shell around the live production site. Cookies, CSRF and the nginx `/api` proxy behave exactly as in a normal browser.

### Testing the new installer

1. Uninstall the previous Kings Grillz SmartPOS completely (Settings → Apps).
2. Download the new `windows-installer` artifact from the latest successful "Build Windows Tauri Installer" run on branch `feature/windows-mobile-release`.
3. Install and launch.
4. You should see the same staff sign-in page as https://kings-grillz.onrender.com.
5. Optional diagnostic: press Ctrl+Shift+I (or right-click → Inspect) and check the address bar / Network tab. Requests to `/api/*` should go to `kings-grillz.onrender.com` and return JSON, not HTML.

### Android

The Capacitor `server.url` was already set to the production frontend and the AndroidManifest includes `INTERNET`. The latest APK should load the live site the same way. Install the newest `android-apk` artifact and test. If it still shows local content, report the exact error.

No production deploy or merge to main is required for this fix.


---

## 15. Customer Change Requests (17 October 2026)

### Official logo
The supplied KING’S GRILLZ logo has been integrated into:
- Staff sign-in page
- Dashboard sidebar
- PWA icons and favicon
- Receipt and invoice PNG generators

Windows and Android app icons still use the previous generated set. The next installer rebuild will pick up any updated icons if they are replaced in the Tauri/Capacitor icon folders.

### Receipts and invoices — PDF and picture
- Existing PDF endpoints remain: `/api/orders/{id}/invoice` and `/api/payments/{id}/receipt`
- New picture endpoints:
  - `/api/orders/{id}/invoice.png`
  - `/api/payments/{id}/receipt.png`
- Pictures are generated with Pillow and include the logo, order number, customer, quantities, prices, delivery, totals and payment status.
- WhatsApp sharing remains a text link plus manual attachment of the downloaded picture or PDF (native share-sheet attachment is not guaranteed on all platforms).

### Editable prices and delivery charges
- Catalogue product price can be updated by an admin via `PATCH /api/products/{id}/price`.
- Order creation accepts an optional `unit_price`. If omitted, the current catalogue price is used.
- Delivery fee is already accepted on order creation and can be any non-negative amount (including 0).
- The agreed unit price and delivery fee are stored on the order at creation time. Later catalogue price changes do not alter existing orders.
- Frontend New Order form now shows an editable Unit Price field that defaults to the current product price.

### Production deployment required
These features live in the backend and frontend source. Because the Windows and Android apps load the live site, the new UI and endpoints will only appear after a controlled production deployment of this branch.

Do not merge to main or deploy to Render until you have reviewed and approved.


# KING'S GRILLZ Receipt Studio — Case Study

A short account of an offline invoice and receipt system built for a Nigerian smoked guinea fowl business. Suitable for a portfolio or a technical introduction. No performance statistics, revenue figures or testimonials are claimed.

## Client problem

Staff needed to produce a branded invoice or receipt for each order. The first version of the product was a cloud system: a React frontend, a FastAPI backend and PostgreSQL on Render, with Tauri and Capacitor shells that loaded the live website. That design kept one shared database, but every document depended on the hosted services. Free-tier cold starts made login unreliable. A desktop or phone that could not reach the server could not produce a receipt.

The business needed a tool that works with no internet and no staff login, on both a Windows PC and an Android phone.

## Solution

Receipt Studio is two independent offline applications that share branding and workflow but not data.

- Create an unpaid invoice or a paid receipt. An invoice is never marked paid unless staff explicitly choose to.
- Product defaults to Signature Smoked Guinea Fowl at ₦14,000. Whole or Chopped. Pickup or Delivery.
- Editable unit price and delivery fee. Historical documents keep the prices they were created with.
- Branded PDF and PNG with the official logo.
- Local history, search and reprint.
- Backup and restore on each device.
- WhatsApp sharing of the document number, total and the PDF.
- Editable PalmPay payment details on invoices only. Receipts do not show bank details.

Windows and Android do not sync. Each device keeps its own SQLite history. Document numbers are prefixed so the two histories cannot be confused: `KG-` on Windows, `KGA-` on Android.

## Technical architecture

| Concern | Choice |
| --- | --- |
| Windows UI | Python 3.12, PySide6 |
| Windows documents | ReportLab (PDF), Pillow (PNG) |
| Windows packaging | PyInstaller, Inno Setup |
| Android UI | Kotlin, Android SDK 34 |
| Android documents | PdfDocument, Canvas PNG |
| Android gallery | MediaStore (Pictures/KingsGrillz) |
| Storage | SQLite on each device |
| Branding | Official circular logo. Black `#171717`, gold `#D9A441`, orange `#E66B24`, cream `#FAF7F0` |

Writable data never lives inside the install folder. On Windows it is in `%APPDATA%\KingsGrillzReceiptStudio\`. On Android it is in the app's private files. The Windows installer upgrades in place and does not touch that folder. The Android APK uses the same application ID and signing certificate as v1.0.0, so it installs as an update.

## Development process

1. The cloud SmartPOS was built and deployed. Cold starts and native packaging showed that a hosted dependency was the wrong fit for receipt work.
2. Receipt Studio was built as a separate offline product. The cloud system was archived, not deleted.
3. v1.0.0 was delivered: Windows installer and a signed Android APK. The customer began using both.
4. v1.0.1 added PalmPay details on invoices, a redesigned Android invoice, Android Gallery saving, and editable payment settings. Existing SQLite histories were preserved. No new signing key was generated.
5. The customer accepted the Android application. The Windows installer was installed successfully.

## Security considerations

- No login and no network are required for core work. There is no staff password to leak and no API token in the apps.
- Payment details are stored locally and are editable by the business owner. They are not hardcoded into document rendering without a way to change them.
- The Android signing keystore is not in the repository. It was delivered outside Git and can be used through GitHub Actions secrets without appearing in code, logs or artifacts.
- The published v1.0.1 APK certificate matches v1.0.0 (SHA256 `F8:85:64:66:EB:41:21:CB:7A:34:3A:CA:F6:7E:75:0A:EA:01:8E:94:57:4F:89:11:B6:CD:99:DC:5E:B5:3C:6A`).
- Uninstalling an app can erase its local history. Staff are instructed to back up before uninstalling.

## Delivery

| Release | Contents |
| --- | --- |
| v1.0.0 | Windows installer and signed Android APK. Offline invoices, receipts, PDF, PNG, history, backup, WhatsApp. |
| v1.0.1 | Same identity. PalmPay section on invoices, redesigned Android invoice, Gallery save, editable payment settings. |

Downloads: [v1.0.1](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/tag/v1.0.1).

## Business benefits

Staff can produce a branded invoice or receipt on the shop PC or a phone without waiting for a server. Payment details can be updated without a developer. Existing records survive upgrades. Windows and Android remain independent, so a problem on one device does not block the other.

## Not claimed

No revenue increase, conversion rate or customer testimonial is stated. Those were not measured as part of this delivery.

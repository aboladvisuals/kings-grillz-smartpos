# Changelog

## v1.0.1 — 18 October 2026

Stable release. Customer accepted the Android application. Windows installer installed successfully.

### Added

- PalmPay payment details section on Windows and Android invoices (bank, account name, account number, payment reference note, unpaid-not-proof note).
- Editable payment settings on both platforms. Defaults: PalmPay, Kings Grillz Ventures, 9552604707.
- Redesigned Android invoice with branding, logo, invoice number, date, customer, itemisation, totals and payment status.
- Android PNG save to Gallery via MediaStore (`Pictures/KingsGrillz`).

### Unchanged

- Receipt design. Receipts do not show bank details.
- Offline operation. No login and no cloud dependency.
- Application ID `com.kingsgrillz.receiptstudio` and the v1.0.0 signing certificate.
- Existing SQLite histories. No destructive migration.

### Downloads

- [Windows installer](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.1/KingsGrillzReceiptStudio-Setup-1.0.1.exe)
- [Android APK](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.1/KingsGrillzReceiptStudio-1.0.1.apk)

## v1.0.0 — 17 October 2026

First accepted release.

### Added

- Offline invoices and receipts on Windows and Android.
- Branded PDF and PNG with the official logo.
- Editable unit price and delivery fee. Historical documents keep their prices.
- Local history, search and reprint.
- Backup and restore on each device.
- WhatsApp sharing.
- Windows installer and signed Android APK.
- No login and no internet required for core work.

### Downloads

- [Windows installer](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.0/KingsGrillzReceiptStudio-Setup-1.0.0.exe)
- [Android APK](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.0/KingsGrillzReceiptStudio-1.0.0.apk)

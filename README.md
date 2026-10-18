# KING'S GRILLZ Receipt Studio

Offline invoice and receipt software for a Nigerian smoked guinea fowl business. Staff can create, save, reprint and share documents with no login and no internet.

**Stable release:** [v1.0.1](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/tag/v1.0.1)

## The problem

The business needed branded invoices and receipts for orders of Signature Smoked Guinea Fowl. An earlier cloud system required a hosted website, an API and a database. When the free hosting tier was cold or unreachable, staff could not produce a document. The business needed a tool that works on a Windows PC and an Android phone with no network.

## The solution

Receipt Studio is two independent offline applications that share the same branding and workflow:

- Create an unpaid **invoice** or a paid **receipt**. Nothing is marked paid automatically.
- Product defaults to Signature Smoked Guinea Fowl at ₦14,000. Whole or Chopped. Pickup or Delivery.
- Editable unit price and delivery fee. Historical documents keep the prices they were created with.
- Branded PDF and PNG export with the official logo.
- Local history, search and reprint.
- Backup and restore on each device.
- WhatsApp sharing. Windows opens the message and the PDF folder. Android uses the native share sheet and can attach the PDF.
- Editable PalmPay payment details on invoices only. Receipts do not show bank details.

## Download v1.0.1

| Platform | File | Link |
| --- | --- | --- |
| Windows | `KingsGrillzReceiptStudio-Setup-1.0.1.exe` | [Download](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.1/KingsGrillzReceiptStudio-Setup-1.0.1.exe) |
| Android | `KingsGrillzReceiptStudio-1.0.1.apk` | [Download](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.1/KingsGrillzReceiptStudio-1.0.1.apk) |
| Release | v1.0.1 | [Release page](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/tag/v1.0.1) |

Previous release: [v1.0.0](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/tag/v1.0.0).

## Install

**Windows.** Run the setup EXE. It installs under Program Files and adds a desktop shortcut. Receipts stay in `%APPDATA%\KingsGrillzReceiptStudio\`, so reinstalling or upgrading does not erase history. Do not uninstall if you want to keep records, unless you have a backup.

**Android.** Install the signed APK over the existing app. Do not uninstall first. Receipts stay in the app's private storage. Uninstalling the app deletes them unless you have a backup. Android numbers look like `KGA-20261018-0001`. Windows numbers look like `KG-20261018-0001`.

## Records are separate

Windows and Android do not sync. A receipt created on one device is not on the other. Back up each device on its own. A Windows `.db` cannot restore an Android history, and the reverse is also true.

## Technology

| App | Stack |
| --- | --- |
| Windows | Python 3.12, PySide6, ReportLab, Pillow, SQLite, PyInstaller, Inno Setup |
| Android | Kotlin, Android SDK 34, SQLite, PdfDocument, MediaStore, native share sheet |
| Branding | Official circular logo. Black `#171717`, gold `#D9A441`, orange `#E66B24`, cream `#FAF7F0` |

## Project structure

```
receipt-studio/          Windows app, tests, installer script
android-receipt-studio/  Android app
docs/                    Customer guide, user guide, case study
.github/workflows/       Windows installer and Android APK builds
```

## Documentation

- [User guide](docs/USER_GUIDE.md) — day-to-day instructions for staff
- [Case study](docs/CASE_STUDY.md) — problem, architecture and delivery
- [Changelog](CHANGELOG.md) — v1.0.0 and v1.0.1

## Develop

```bash
cd receipt-studio
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m kings_grillz
```

## Delivered vs future

**Delivered in v1.0.1**

- Offline invoices and receipts on Windows and Android
- Branded PDF and PNG
- Editable unit price, delivery fee and PalmPay payment details
- Android PNG save to Gallery
- Local history, search, backup and restore
- WhatsApp sharing
- Signed Android update that installs over v1.0.0

**Not in this release**

- Cloud sync between Windows and Android
- Online payment collection
- Multi-user login
- Automatic paid status

## Archived cloud product

An earlier SmartPOS (React, FastAPI, Tauri, Capacitor, Render) is preserved and is not the active product:

- Branch: `archive/smartpos-cloud-2026-10-17`
- Tag: `archive-smartpos-cloud-2026-10-17`

Do not delete the archive without explicit approval.

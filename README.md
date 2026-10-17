# KING'S GRILLZ Receipt Studio

Offline invoices and receipts for a Nigerian smoked guinea fowl business. Version 1.0.0 was accepted by the client.

No login, internet, or cloud service is required to create, save, or reprint a receipt.

## Download v1.0.0

- Windows installer: [KingsGrillzReceiptStudio-Setup-1.0.0.exe](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.0/KingsGrillzReceiptStudio-Setup-1.0.0.exe)
- Signed Android APK: [KingsGrillzReceiptStudio-1.0.0.apk](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.0/KingsGrillzReceiptStudio-1.0.0.apk)
- Release page: [v1.0.0](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/tag/v1.0.0)

## Install

**Windows:** run the setup EXE. It installs under Program Files and adds a desktop shortcut. Receipts stay in `%APPDATA%\KingsGrillzReceiptStudio\`, so reinstalling does not erase history.

**Android:** install the signed APK. Allow the browser or Files app if Android asks. Receipts stay in the app's private storage. Uninstalling the app deletes them unless you have a backup.

## What it does offline

- Create an unpaid invoice or a paid receipt. Nothing is marked paid automatically.
- Product: Signature Smoked Guinea Fowl. Default price ₦14,000. Whole or Chopped. Pickup or Delivery.
- Editable unit price and delivery fee.
- Export a branded PDF and PNG.
- Local history, search, and reprint.
- Backup and restore on each device.
- Share to WhatsApp. Windows opens the message and the PDF folder. Android uses the native share sheet and can attach the PDF.

## Records are separate

Windows and Android do not sync.

| Device | Number example | Storage |
| --- | --- | --- |
| Windows | `KG-20261017-0001` | `%APPDATA%\KingsGrillzReceiptStudio\` |
| Android | `KGA-20261017-0001` | App private files |

Back up each device on its own. A Windows `.db` cannot restore an Android history, and the reverse is also true.

Staff instructions: `docs/CUSTOMER_GUIDE.md`.

## Technology

| App | Stack |
| --- | --- |
| Windows | Python 3.12, PySide6, ReportLab, Pillow, SQLite, PyInstaller, Inno Setup |
| Android | Kotlin, Android SDK 34, SQLite, PdfDocument, native share sheet |
| Branding | Official circular logo. Black `#171717`, gold `#D9A441`, orange `#E66B24`, cream `#FAF7F0` |

## Project structure

```
receipt-studio/          Windows app, tests, installer script
android-receipt-studio/  Android app
docs/                    Customer guide, case study, handover, retirement checklist
.github/workflows/       Windows installer and Android APK builds
```

## Develop

```bash
cd receipt-studio
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m kings_grillz
```

## Archived cloud product

The earlier SmartPOS (React, FastAPI, Tauri, Capacitor, Render) is not the active product. It is preserved:

- Branch: `archive/smartpos-cloud-2026-10-17`
- Tag: `archive-smartpos-cloud-2026-10-17`

Do not delete the archive, this repository, the Render services, or the production PostgreSQL database without explicit approval. Customer records from the cloud period live only in that database. The free PostgreSQL instance expires on 15 November 2026.

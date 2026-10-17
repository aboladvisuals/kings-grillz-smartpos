# KING'S GRILLZ Receipt Studio — Case Study

**Client:** a Nigerian premium smoked guinea fowl business  
**Product delivered:** offline Windows and Android receipt applications, v1.0.0  
**Outcome:** accepted by the client for daily invoice and receipt work  
**Repository:** https://github.com/aboladvisuals/kings-grillz-smartpos  
**Release:** https://github.com/aboladvisuals/kings-grillz-smartpos/releases/tag/v1.0.0

## Business problem

Staff needed to issue a branded invoice or a paid receipt at the point of sale, then send it to the customer on WhatsApp. The catalogue was simple: Signature Smoked Guinea Fowl at a default of ₦14,000, prepared Whole or Chopped, collected by Pickup or Delivery.

An early cloud system could do this, but it depended on a hosted website, an API, and a PostgreSQL database. Free-tier cold starts made login unreliable. A desktop or phone that could not reach the server could not produce a receipt. The business needed a tool that worked with no internet and no staff login.

## Requirements that shipped

- Branded invoice and receipt, with a clear unpaid versus paid distinction
- Never mark an invoice paid unless staff explicitly choose to
- Editable product price and delivery charge, without changing historical documents
- PDF and PNG export with the official logo
- WhatsApp sharing of the document number, total, and the PDF
- Local history, search, and reprint
- Backup and restore
- Windows installer and a signed Android APK
- No login, no API, and no cloud dependency for core work

## First architecture: cloud SmartPOS

The first product was a same-origin web system:

- React and Vite frontend
- FastAPI backend
- PostgreSQL on Render
- nginx proxy so the browser called `/api` and kept cookie sessions
- Tauri desktop shell and a Capacitor Android shell that loaded the live website

That design protected staff routes and kept one database of customers and orders. It also tied every receipt to the hosted services. When those services were cold or unreachable, the apps failed. Native packaging added a second problem: relative API calls inside a desktop or phone shell did not behave like the browser.

That cloud product is preserved, not deleted:

- Branch `archive/smartpos-cloud-2026-10-17`
- Tag `archive-smartpos-cloud-2026-10-17`
- Render services and the production database were left in place

## Migration: offline Receipt Studio

The active product is two local applications that share branding and business rules, not a database.

**Windows** is a Python application:

- PySide6 for the interface
- ReportLab for PDF
- Pillow for PNG
- SQLite for history and settings
- PyInstaller for the executable
- Inno Setup for the installer
- Writable data in `%APPDATA%\KingsGrillzReceiptStudio\`, not inside the install folder

**Android** is a Kotlin application:

- Local SQLite
- Android `PdfDocument` and bitmap export
- Native share sheet, so WhatsApp can receive the PDF when the device supports it
- Receipt numbers prefixed `KGA-` so they cannot collide with Windows `KG-` numbers

Core generation does not call Render, does not log in, and does not need a network. Opening WhatsApp is the only step that uses the internet.

## Implemented features

- Official logo and brand colours on screen and on documents
- Invoice stays unpaid; receipt is created only when staff choose paid, or when they explicitly mark an invoice paid
- Default product and price, with delivery fee applied only for Delivery
- PDF and PNG that include document number, customer, preparation, fulfilment, totals, and paid or unpaid status
- Windows Save As to any folder; history still kept in AppData
- Windows WhatsApp flow prepares the number and message, then opens the PDF folder because Windows cannot attach the file automatically
- Android WhatsApp flow uses the system share sheet with the PDF attached where the target app accepts it
- Searchable local history and reprint
- Backup and restore on each platform
- Automated Windows tests for numbering, unpaid versus paid, settings, PDF and PNG output, and backup
- Windows packaged executable smoke-tested in CI before the installer was published
- Signed Android release APK, not a debug build
- Versioned GitHub Release v1.0.0 containing both customer installers

## Release and handover

v1.0.0 was published with:

- `KingsGrillzReceiptStudio-Setup-1.0.0.exe`
- `KingsGrillzReceiptStudio-1.0.0.apk`

The client accepted both applications after manual testing. Customer instructions are in `docs/CUSTOMER_GUIDE.md`. A retirement checklist for the old Render services exists and has not been executed.

## What was deliberately not done

These are future possibilities, not delivered features:

- Sync between Windows and Android
- Multi-user login or roles in Receipt Studio
- Automatic attachment of the PDF inside the Windows WhatsApp window
- Migration of historical cloud orders into the offline apps
- Shutdown or deletion of Render or the production PostgreSQL database
- Play Store distribution

Windows and Android histories remain separate unless a future sync is explicitly built.

## Stack summary

| Concern | Choice |
| --- | --- |
| Windows UI | PySide6 |
| Windows documents | ReportLab, Pillow |
| Windows packaging | PyInstaller, Inno Setup |
| Android UI and documents | Kotlin, PdfDocument |
| Persistence | SQLite on each device |
| Sharing | WhatsApp link on Windows; Android share sheet |
| Old cloud system | React, FastAPI, PostgreSQL, Tauri, Capacitor — archived |

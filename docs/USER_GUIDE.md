# KING'S GRILLZ Receipt Studio — User Guide

Simple instructions for staff. Version 1.0.1. No login and no internet are required.

## Create an invoice or receipt

1. Open KING'S GRILLZ on Windows or Android.
2. Enter the customer name and phone.
3. Confirm the product (default: Signature Smoked Guinea Fowl), quantity and unit price.
4. Choose Whole or Chopped.
5. Choose Pickup or Delivery. If Delivery, enter the delivery fee.
6. Choose Invoice (unpaid) or Receipt (paid).
7. Save PDF or Save PNG.

An invoice stays unpaid until you explicitly create a receipt or mark it paid. An unpaid invoice is not proof of payment.

## Payment details (invoices only)

Invoices show a payment section:

- Bank: PalmPay
- Account name: Kings Grillz Ventures
- Account number: 9552604707

These are the defaults. The business owner can change them:

- **Windows:** open Settings, edit Bank name, Account name and Account number, then Save settings.
- **Android:** tap Payment settings, edit the three fields, then Save.

Changes apply to newly generated invoices. Old documents are not rewritten. Receipts do not show bank details.

## Save and share

- **PDF:** Save PDF. On Android, share to WhatsApp can attach the PDF.
- **PNG:** Save PNG. On Android, the image is also saved to the phone Gallery under Pictures/KingsGrillz.
- **WhatsApp:** Windows opens the message and the PDF folder. Attach the PDF yourself. Android uses the share sheet and can attach the PDF.

## Protect records

Windows and Android keep separate histories. A document on the PC is not on the phone.

- Back up each device on its own.
- A Windows backup cannot restore an Android phone, and the reverse is also true.
- Uninstalling an app may erase its local records unless you have a backup.

**Windows backup.** Use the backup option in the app, or copy `%APPDATA%\KingsGrillzReceiptStudio\`.

**Android backup.** Tap Backup database and save the file somewhere safe (for example WhatsApp or Files). Restore later with Restore database.

## Update without losing records

**Windows.** Download and run [KingsGrillzReceiptStudio-Setup-1.0.1.exe](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.1/KingsGrillzReceiptStudio-Setup-1.0.1.exe). Install over the existing program. Do not uninstall first. History stays in `%APPDATA%\KingsGrillzReceiptStudio\`.

**Android.** Download [KingsGrillzReceiptStudio-1.0.1.apk](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.1/KingsGrillzReceiptStudio-1.0.1.apk) and install it. Android will offer to update the existing app. Do not uninstall first.

## Document numbers

| Device | Example |
| --- | --- |
| Windows | `KG-20261018-0001` |
| Android | `KGA-20261018-0001` |

## If something goes wrong

- The app will not open: restart the device and try again.
- Android will not update: confirm you are installing the signed v1.0.1 APK, not an unsigned test build.
- Gallery does not show the PNG: open the Gallery app and look in Pictures/KingsGrillz, or check that storage permission was granted.
- History is missing after uninstall: restore from the backup you made before uninstalling.

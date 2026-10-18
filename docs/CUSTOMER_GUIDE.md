# KING'S GRILLZ Receipt Studio — Customer Guide

Offline invoices and receipts for Windows and Android, version 1.0.1. No login and no internet are required.

## What's new in 1.0.1

- Windows invoices now include a professional PalmPay payment details section.
- Android invoices have been redesigned to match a commercial business invoice, including payment details.
- Android PNG can be saved directly to the phone Gallery.
- Business owner can edit bank name, account name and account number in Settings (Windows) or Payment settings (Android).
- Receipts are unchanged and do not show bank details.
- Existing history is preserved. Install as an update — do not uninstall.


## Important: records are separate

Windows and Android each keep their own receipt history on that device.

- A receipt created on Windows is not on the phone.
- A receipt created on Android is not on the PC.
- There is no cloud sync.
- Windows numbers look like `KG-20261017-0001`.
- Android numbers look like `KGA-20261017-0001`.

Back up each device separately.

## Windows

1. Download [KingsGrillzReceiptStudio-Setup-1.0.0.exe](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.0/KingsGrillzReceiptStudio-Setup-1.0.0.exe).
2. Run the installer.
3. Open KING'S GRILLZ Receipt Studio from the desktop or Start menu.
4. Enter customer name and phone, product, quantity and price.
5. Choose Whole or Chopped, Pickup or Delivery, Invoice (unpaid) or Receipt (paid).
6. Save PDF, Save PNG, Save As, or Share to WhatsApp.

Data stays in `%APPDATA%\KingsGrillzReceiptStudio\`.

WhatsApp opens the message. Attach the PDF from the folder that opens. Windows cannot attach it automatically.

## Android

1. Download the signed release [KingsGrillzReceiptStudio-1.0.0.apk](https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.0/KingsGrillzReceiptStudio-1.0.0.apk).
2. Allow install from the browser or Files if Android asks.
3. Install and open KING'S GRILLZ.
4. Create the invoice or receipt. It works with airplane mode on.
5. Share to WhatsApp uses the phone share sheet and can attach the PDF.

Android stores receipts in the app's private files. Uninstalling the app deletes them unless you have a backup.

## Backup and recovery

### Windows
- In the app, History → Backup. A copy is saved under `%APPDATA%\KingsGrillzReceiptStudio\backups\`.
- To restore: History → Restore, and choose that `.db` file.
- You can also copy the whole `%APPDATA%\KingsGrillzReceiptStudio\` folder to a USB drive.

### Android
- Tap **Backup database** and send `receipts-backup.db` to Drive, WhatsApp or a computer.
- Tap **Restore database**, choose that `.db` file, and confirm. This replaces the phone's current history with the backup.
- Restore only a backup made by this app. Windows backups are not interchangeable.

## Acceptance checklist

- [ ] Windows app opens with no internet
- [ ] Android app opens with no internet
- [ ] Create an unpaid invoice on each device
- [ ] Create a paid receipt on each device
- [ ] PDF opens and shows the logo, number and total
- [ ] PNG opens
- [ ] WhatsApp message includes the number and total
- [ ] PDF can be attached (folder on Windows, share sheet on Android)
- [ ] History shows the new document after restart
- [ ] Backup file is created on each device
- [ ] Android restore replaces history with the chosen backup
- [ ] Windows number starts with `KG-`
- [ ] Android number starts with `KGA-`

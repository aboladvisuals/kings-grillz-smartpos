# KING'S GRILLZ Receipt Studio — Customer Guide

Offline invoices and receipts for Windows and Android. No login and no internet are required to create a receipt.

## Important: records are separate

Windows and Android each keep their own receipt history on that device.

- A receipt created on Windows is not on the phone.
- A receipt created on Android is not on the PC.
- There is no cloud sync.
- Windows numbers look like `KG-20261017-0001`.
- Android numbers look like `KGA-20261017-0001`.

Back up each device separately.

## Windows

1. Download the artifact `kings-grillz-receipt-studio-windows` from the Windows workflow.
2. Extract the folder.
3. Run `KingsGrillzReceiptStudio.exe`.
4. Enter customer name and phone, product, quantity and price.
5. Choose Whole or Chopped, Pickup or Delivery, Invoice (unpaid) or Receipt (paid).
6. Save PDF, Save PNG, Save As, or Share to WhatsApp.

Data stays in `%APPDATA%\KingsGrillzReceiptStudio\`.

WhatsApp opens the message. Attach the PDF from the folder that opens. Windows cannot attach it automatically.

## Android

1. Download `kings-grillz-receipt-studio-android` (`app-debug.apk`).
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
- Tap Backup database and send the file to Drive, WhatsApp or a computer.
- To recover after reinstall, keep that backup file. Restoring over a live database should be done only when you intend to replace the phone's history.

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
- [ ] Windows number starts with `KG-`
- [ ] Android number starts with `KGA-`

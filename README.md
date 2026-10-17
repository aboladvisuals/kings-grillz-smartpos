# KING'S GRILLZ Receipt Studio

Offline Windows application for branded invoices and receipts.

No internet, login, or cloud service is required to create, save, or reprint receipts.

## Use the app

1. Download the Windows build from the [Receipt Studio workflow](https://github.com/aboladvisuals/kings-grillz-smartpos/actions/workflows/receipt-studio-windows.yml).
2. Extract the artifact `kings-grillz-receipt-studio-windows`.
3. Run `KingsGrillzReceiptStudio.exe`.

Receipts are stored in `%APPDATA%\KingsGrillzReceiptStudio\`. Reinstalling the program does not erase history.

## Develop

```bash
cd receipt-studio
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m kings_grillz
```

Android APK: workflow `Build Receipt Studio Android`, artifact `kings-grillz-receipt-studio-android`.

Windows and Android histories are separate. See `docs/CUSTOMER_GUIDE.md`.

See `receipt-studio/USER_GUIDE.md` for the Windows staff guide.

## What is archived

The previous cloud SmartPOS (React, FastAPI, Tauri, Capacitor, Render) is preserved and is not the active product.

- Archive branch: `archive/smartpos-cloud-2026-10-17`
- Archive tag: `archive-smartpos-cloud-2026-10-17`
- Full Git history is retained

Do not delete the archive, the repository, Render services, or the production PostgreSQL database without explicit approval. Production customer records still live only in that database.

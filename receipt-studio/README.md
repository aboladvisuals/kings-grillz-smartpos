# KING'S GRILLZ Receipt Studio

Offline Windows application for branded invoices and receipts.

No internet, login, or cloud service is required for core operations.

## Run from source

```bash
cd receipt-studio
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m kings_grillz
```

## Data location

Writable data is stored in the user application-data folder:

- Windows: `%APPDATA%\KingsGrillzReceiptStudio\`
- Database: `receipts.db`
- Exports: `exports\`
- Backups: `backups\`

Reinstalling the program does not erase history.

## Build Windows installer

On a Windows machine, or via the GitHub Actions workflow:

```powershell
cd receipt-studio
pip install -r requirements.txt
pyinstaller --noconfirm --windowed --name "KingsGrillzReceiptStudio" --add-data "assets;assets" --icon assets\logo.png kings_grillz\__main__.py
```

The executable is produced under `dist\KingsGrillzReceiptStudio\`.

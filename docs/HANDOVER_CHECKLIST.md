# KING'S GRILLZ Receipt Studio — Final handover

Version 1.0.0. Active product is the offline Receipt Studio.

## Delivered

- Windows installer: https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.0/KingsGrillzReceiptStudio-Setup-1.0.0.exe
- Android signed release APK: https://github.com/aboladvisuals/kings-grillz-smartpos/releases/download/v1.0.0/KingsGrillzReceiptStudio-1.0.0.apk
- Source on `main`: `receipt-studio/`, `android-receipt-studio/`, `docs/`
- Archive of the old cloud SmartPOS: branch `archive/smartpos-cloud-2026-10-17`, tag `archive-smartpos-cloud-2026-10-17`
- Customer guide: `docs/CUSTOMER_GUIDE.md`
- Render retirement checklist: `docs/RENDER_RETIREMENT_CHECKLIST.md` (not executed)

## Customer must keep

- The Android signing keystore, delivered outside Git. Losing it means future APK updates cannot be installed over this one.
- Windows backups from `%APPDATA%\KingsGrillzReceiptStudio\`
- Android backup `.db` files
- The production PostgreSQL export, if the old cloud history is still needed

## Confirmed separate

Windows (`KG-`) and Android (`KGA-`) histories are not synced.

## Not deleted

GitHub repository, archive branch, archive tag, Render services, PostgreSQL, and existing backups.

"""Application data locations. Writable data never lives inside the install folder."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "KingsGrillzReceiptStudio"


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def resource_dir() -> Path:
    """Bundled read-only assets (logo, etc.)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def app_data_dir() -> Path:
    """User-writable directory that survives upgrades and reinstalls."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return app_data_dir() / "receipts.db"


def backup_dir() -> Path:
    path = app_data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def export_dir() -> Path:
    path = app_data_dir() / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logo_path() -> Path:
    bundled = resource_dir() / "assets" / "logo.png"
    if bundled.exists():
        return bundled
    return resource_dir() / "logo.png"

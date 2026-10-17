"""WhatsApp sharing helpers. Receipt generation stays offline; opening WhatsApp needs internet."""

from __future__ import annotations

import re
import urllib.parse
import webbrowser
from pathlib import Path

from .database import Document
from .pdf import naira


def normalize_whatsapp_number(phone: str) -> str:
    """Return digits suitable for wa.me. Nigerian local numbers become 234…"""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = "234" + digits[1:]
    if len(digits) < 8:
        raise ValueError("Enter a valid customer phone number for WhatsApp.")
    return digits


def receipt_message(doc: Document) -> str:
    kind = "receipt" if doc.payment_status == "paid" else "invoice"
    status = "PAID" if doc.payment_status == "paid" else "UNPAID"
    return (
        f"Hello {doc.customer_name},\n\n"
        f"Thank you for choosing KING'S GRILLZ.\n"
        f"Your {kind} {doc.number} is ready.\n"
        f"Total: {naira(doc.total)}\n"
        f"Status: {status}\n\n"
        f"The PDF is attached. Please keep it for your records."
    )


def whatsapp_url(doc: Document) -> str:
    number = normalize_whatsapp_number(doc.customer_phone)
    text = urllib.parse.quote(receipt_message(doc))
    return f"https://wa.me/{number}?text={text}"


def open_whatsapp(doc: Document) -> str:
    url = whatsapp_url(doc)
    webbrowser.open(url)
    return url


def open_folder(path: Path) -> None:
    """Reveal the file's folder so staff can attach it. Windows has no reliable auto-attach."""
    folder = path if path.is_dir() else path.parent
    import os
    import sys
    if sys.platform == "win32":
        os.startfile(folder)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        import subprocess
        subprocess.Popen(["open", str(folder)])
    else:
        import subprocess
        subprocess.Popen(["xdg-open", str(folder)])

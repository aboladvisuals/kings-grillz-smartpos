"""High-quality PNG invoice and receipt images."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .database import Document
from .paths import logo_path
from .pdf import naira


BLACK = (23, 23, 23)
GOLD = (217, 164, 65)
ORANGE = (230, 107, 36)
CREAM = (250, 247, 240)
GREEN = (27, 122, 58)
WHITE = (255, 255, 255)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def build_png(doc: Document) -> Image.Image:
    width, height = 900, 1280
    image = Image.new("RGB", (width, height), CREAM)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 16), fill=GOLD)
    logo = logo_path()
    y = 40
    if logo.exists():
        mark = Image.open(logo).convert("RGBA").resize((140, 140))
        image.paste(mark, ((width - 140) // 2, y), mark)
        y += 160
    draw.text((width // 2, y), "KING'S GRILLZ", fill=GOLD, font=_font(36, True), anchor="mm")
    y += 36
    draw.text((width // 2, y), "YOUR PREMIUM AWO PLUG", fill=BLACK, font=_font(16), anchor="mm")
    y += 40
    is_paid = doc.payment_status == "paid"
    title = "RECEIPT" if is_paid else "INVOICE"
    draw.text((width // 2, y), title, fill=BLACK, font=_font(28, True), anchor="mm")
    y += 34
    status = "PAID" if is_paid else "UNPAID"
    draw.text((width // 2, y), status, fill=GREEN if is_paid else ORANGE, font=_font(20, True), anchor="mm")
    y += 50

    rows = [
        ("Document", doc.number),
        ("Date", doc.created_at.replace("T", " ")),
        ("Customer", doc.customer_name),
        ("Phone", doc.customer_phone),
        ("Product", doc.product_name),
        ("Preparation", doc.preparation),
        ("Fulfilment", doc.fulfilment),
        ("Quantity", str(doc.quantity)),
        ("Unit price", naira(doc.unit_price)),
        ("Subtotal", naira(doc.subtotal)),
        ("Delivery fee", naira(doc.delivery_fee)),
        ("Total", naira(doc.total)),
        ("Amount paid", naira(doc.amount_paid)),
        ("Balance due", naira(max(doc.total - doc.amount_paid, 0))),
    ]
    for label, value in rows:
        draw.text((70, y), label, fill=(102, 102, 102), font=_font(18), anchor="lm")
        draw.text((width - 70, y), value, fill=BLACK, font=_font(18, True), anchor="rm")
        y += 36
    if doc.notes:
        y += 10
        draw.text((70, y), f"Notes: {doc.notes}", fill=BLACK, font=_font(16), anchor="lm")
        y += 40
    y += 20
    draw.text((width // 2, y), "Thank you for choosing KING'S GRILLZ!", fill=GOLD, font=_font(18, True), anchor="mm")
    draw.rectangle((0, height - 16, width, height), fill=GOLD)
    return image


def write_png(doc: Document, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    build_png(doc).save(destination, "PNG")
    return destination

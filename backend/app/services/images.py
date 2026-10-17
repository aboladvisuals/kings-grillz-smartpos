"""Generate PNG receipts and invoices using Pillow.

Reuses the same monetary data as the PDF generators so totals always agree.
"""
from io import BytesIO
from pathlib import Path
from datetime import timezone
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo.png"


def naira(amount: int) -> str:
    return f"₦{amount:,.2f}"


def _font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_header(draw: ImageDraw.ImageDraw, img: Image.Image, title: str, y: int) -> int:
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo.thumbnail((120, 120), Image.Resampling.LANCZOS)
        img.paste(logo, ((img.width - logo.width) // 2, y), logo)
        y += logo.height + 12
    draw.text((img.width // 2, y), "KING'S GRILLZ", fill=(217, 164, 65), font=_font(22, True), anchor="mm")
    y += 32
    draw.text((img.width // 2, y), title, fill=(23, 23, 23), font=_font(16, True), anchor="mm")
    return y + 28


def generate_receipt_image(payment, order, customer) -> BytesIO:
    """Portrait PNG receipt matching PDF content."""
    width, height = 600, 900
    img = Image.new("RGB", (width, height), (250, 247, 240))
    draw = ImageDraw.Draw(img)

    y = 24
    y = _draw_header(draw, img, "PAYMENT RECEIPT", y)

    lagos = order.created_at.astimezone(ZoneInfo("Africa/Lagos")) if order.created_at else None
    date_str = lagos.strftime("%d %b %Y, %H:%M") if lagos else "—"

    lines = [
        ("Receipt No.", f"KG-R-{payment.id:05d}"),
        ("Order No.", order.order_number),
        ("Date", date_str),
        ("Customer", customer.name if customer else "—"),
        ("Phone", customer.phone if customer else "—"),
        ("", ""),
        ("Quantity", str(order.quantity)),
        ("Unit Price", naira(order.unit_price)),
        ("Subtotal", naira(order.subtotal)),
        ("Delivery", naira(order.delivery_fee)),
        ("Total", naira(order.total)),
        ("Amount Paid", naira(payment.amount)),
        ("Balance Due", naira(getattr(payment, "_balance_after", order.total - order.amount_paid))),
        ("Payment Status", order.payment_status.upper()),
    ]

    for label, value in lines:
        if not label:
            y += 8
            continue
        draw.text((40, y), label, fill=(100, 100, 100), font=_font(12))
        draw.text((width - 40, y), value, fill=(23, 23, 23), font=_font(12, True), anchor="ra")
        y += 28

    y += 20
    status = "PAID IN FULL" if order.payment_status == "paid" else "PARTIAL / UNPAID"
    color = (40, 140, 60) if order.payment_status == "paid" else (180, 80, 20)
    draw.text((width // 2, y), status, fill=color, font=_font(14, True), anchor="mm")

    buf = BytesIO()
    img.save(buf, "PNG", optimize=True)
    buf.seek(0)
    return buf


def generate_invoice_image(order, customer, product) -> BytesIO:
    """Portrait PNG invoice matching PDF content."""
    width, height = 600, 900
    img = Image.new("RGB", (width, height), (250, 247, 240))
    draw = ImageDraw.Draw(img)

    y = 24
    title = "INVOICE" if order.payment_status != "paid" else "PAID INVOICE"
    y = _draw_header(draw, img, title, y)

    lagos = order.created_at.astimezone(ZoneInfo("Africa/Lagos")) if order.created_at else None
    date_str = lagos.strftime("%d %b %Y, %H:%M") if lagos else "—"

    lines = [
        ("Invoice No.", order.order_number),
        ("Date", date_str),
        ("Customer", customer.name if customer else "—"),
        ("Phone", customer.phone if customer else "—"),
        ("Product", product.name if product else "—"),
        ("", ""),
        ("Quantity", str(order.quantity)),
        ("Unit Price", naira(order.unit_price)),
        ("Subtotal", naira(order.subtotal)),
        ("Delivery Fee", naira(order.delivery_fee)),
        ("Total", naira(order.total)),
        ("Amount Paid", naira(order.amount_paid)),
        ("Balance Due", naira(order.total - order.amount_paid)),
        ("Status", order.payment_status.upper()),
    ]

    for label, value in lines:
        if not label:
            y += 8
            continue
        draw.text((40, y), label, fill=(100, 100, 100), font=_font(12))
        draw.text((width - 40, y), value, fill=(23, 23, 23), font=_font(12, True), anchor="ra")
        y += 28

    y += 16
    note = "This is an invoice. Payment is outstanding." if order.payment_status != "paid" else "Payment received in full."
    draw.text((width // 2, y), note, fill=(100, 100, 100), font=_font(11), anchor="mm")

    buf = BytesIO()
    img.save(buf, "PNG", optimize=True)
    buf.seek(0)
    return buf

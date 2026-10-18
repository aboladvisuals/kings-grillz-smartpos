"""Professional branded PDF invoices and receipts."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .database import Document, load_settings
from .paths import logo_path


BLACK = colors.HexColor("#171717")
GOLD = colors.HexColor("#D9A441")
ORANGE = colors.HexColor("#E66B24")
CREAM = colors.HexColor("#FAF7F0")
GREY = colors.HexColor("#666666")


def naira(amount: int) -> str:
    return f"₦{amount:,.0f}"


def build_pdf(doc: Document, bank_name: str = "", account_name: str = "", account_number: str = "") -> bytes:
    buffer = BytesIO()
    is_paid = doc.payment_status == "paid"
    title = "RECEIPT" if is_paid else "INVOICE"
    story_doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"KING'S GRILLZ {title} {doc.number}",
        author="KING'S GRILLZ",
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    styles = {
        "brand": ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=18, textColor=GOLD, alignment=TA_CENTER, leading=22),
        "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=9, textColor=GREY, alignment=TA_CENTER, leading=12),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=14, textColor=BLACK, alignment=TA_CENTER, spaceBefore=6, spaceAfter=4),
        "status": ParagraphStyle("status", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#1B7A3A") if is_paid else ORANGE, alignment=TA_CENTER),
        "label": ParagraphStyle("label", fontName="Helvetica", fontSize=9, textColor=GREY),
        "value": ParagraphStyle("value", fontName="Helvetica-Bold", fontSize=10, textColor=BLACK),
        "thanks": ParagraphStyle("thanks", fontName="Helvetica-Oblique", fontSize=9, textColor=GREY, alignment=TA_CENTER, spaceBefore=8),
    }
    story = []
    logo = logo_path()
    if logo.exists():
        story.append(Image(str(logo), width=28 * mm, height=28 * mm, hAlign="CENTER"))
        story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("KING'S GRILLZ", styles["brand"]))
    story.append(Paragraph("YOUR PREMIUM AWO PLUG", styles["sub"]))
    story.append(Paragraph(title, styles["title"]))
    story.append(Paragraph("PAID" if is_paid else "UNPAID", styles["status"]))
    story.append(Spacer(1, 4 * mm))

    meta = [
        [Paragraph("Document", styles["label"]), Paragraph(doc.number, styles["value"])],
        [Paragraph("Date", styles["label"]), Paragraph(doc.created_at.replace("T", " "), styles["value"])],
        [Paragraph("Customer", styles["label"]), Paragraph(doc.customer_name, styles["value"])],
        [Paragraph("Phone", styles["label"]), Paragraph(doc.customer_phone, styles["value"])],
        [Paragraph("Preparation", styles["label"]), Paragraph(doc.preparation, styles["value"])],
        [Paragraph("Fulfilment", styles["label"]), Paragraph(doc.fulfilment, styles["value"])],
    ]
    meta_table = Table(meta, colWidths=[40 * mm, 120 * mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 0.4, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 5 * mm))

    items = [
        [Paragraph("Item", styles["value"]), Paragraph("Qty", styles["value"]),
         Paragraph("Price", styles["value"]), Paragraph("Amount", styles["value"])],
        [Paragraph(doc.product_name, styles["label"]), Paragraph(str(doc.quantity), styles["label"]),
         Paragraph(naira(doc.unit_price), styles["label"]), Paragraph(naira(doc.subtotal), styles["label"])],
    ]
    item_table = Table(items, colWidths=[80 * mm, 20 * mm, 30 * mm, 30 * mm])
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), GOLD),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.4, BLACK),
        ("LINEBELOW", (0, 0), (-1, 0), 1, GOLD),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 4 * mm))

    totals = [
        ["Subtotal", naira(doc.subtotal)],
        ["Delivery fee", naira(doc.delivery_fee)],
        ["Total", naira(doc.total)],
        ["Amount paid", naira(doc.amount_paid)],
        ["Balance due", naira(max(doc.total - doc.amount_paid, 0))],
    ]
    total_table = Table(totals, colWidths=[130 * mm, 30 * mm])
    total_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 2), (-1, 2), BLACK),
        ("LINEABOVE", (0, 2), (-1, 2), 0.6, GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(total_table)
    if doc.notes:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(f"Notes: {doc.notes}", styles["label"]))
    # Payment details on invoices only (not receipts)
    if not is_paid and (bank_name or account_name or account_number):
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph("PAYMENT DETAILS", styles["value"]))
        pay_rows = [
            ["Bank", bank_name or "—"],
            ["Account name", account_name or "—"],
            ["Account number", account_number or "—"],
        ]
        pay_table = Table(pay_rows, colWidths=[50 * mm, 110 * mm])
        pay_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CREAM),
            ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(pay_table)
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            "Please use your invoice number as the payment reference.",
            styles["label"],
        ))
        story.append(Paragraph(
            "An unpaid invoice is not proof of payment.",
            styles["label"],
        ))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Thank you for choosing KING'S GRILLZ!", styles["thanks"]))

    story_doc.build(story)
    return buffer.getvalue()


def write_pdf(doc: Document, destination: Path, bank_name: str = "", account_name: str = "", account_number: str = "") -> Path:
    if not (bank_name or account_name or account_number):
        try:
            s = load_settings()
            bank_name, account_name, account_number = s.bank_name, s.account_name, s.account_number
        except Exception:
            pass
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(build_pdf(doc, bank_name, account_name, account_number))
    return destination

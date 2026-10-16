
from io import BytesIO
from datetime import timezone
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


BLACK = colors.HexColor("#171717")
GOLD = colors.HexColor("#D9A441")
CREAM = colors.HexColor("#FAF7F0")
GREY = colors.HexColor("#666666")


def register_fonts():
    choices = [
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]

    for regular, bold in choices:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(
                TTFont("ReceiptRegular", str(regular))
            )
            pdfmetrics.registerFont(
                TTFont("ReceiptBold", str(bold))
            )
            return

    raise RuntimeError("Unicode font not found")


register_fonts()


def money(amount):
    return f"₦{amount:,.2f}"


def generate_receipt(payment, order, customer):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Payment Receipt KG-R-{payment.id:05d}",
    )

    title_style = ParagraphStyle(
        "ReceiptTitle",
        fontName="ReceiptBold",
        fontSize=24,
        leading=30,
        textColor=GOLD,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "ReceiptHeading",
        fontName="ReceiptBold",
        fontSize=15,
        leading=22,
        textColor=BLACK,
    )

    body_style = ParagraphStyle(
        "ReceiptBody",
        fontName="ReceiptRegular",
        fontSize=10,
        leading=17,
        textColor=BLACK,
    )

    center_style = ParagraphStyle(
        "ReceiptCenter",
        parent=body_style,
        alignment=TA_CENTER,
    )

    story = [
        Paragraph("KING'S GRILLZ", title_style),
        Paragraph("YOUR PREMIUM AWO PLUG", center_style),
        Paragraph("33 Kayode Arikawe Street", center_style),
        Spacer(1, 12 * mm),
        Paragraph("PAYMENT RECEIPT", heading_style),
        Spacer(1, 7 * mm),
    ]

    created = payment.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    date = created.astimezone(
        ZoneInfo("Africa/Lagos")
    ).strftime("%d %B %Y, %I:%M %p")

    # Calculate balance at the time of this payment.
    # Earlier confirmed payments have smaller IDs.
    from sqlalchemy import select, func

    # The endpoint supplies the historical balance.
    balance_after = getattr(
        payment,
        "_balance_after",
        order.total - order.amount_paid,
    )

    details = [
        ["Receipt Number", f"KG-R-{payment.id:05d}"],
        ["Order Number", order.order_number],
        ["Date", date],
        ["Customer", customer.name],
        ["Phone", customer.phone],
        ["Payment Method", payment.method],
        ["Payment Reference", payment.reference],
        ["Payment Status", payment.status.upper()],
    ]

    rows = [
        [
            Paragraph(
                escape(str(label)),
                body_style,
            ),
            Paragraph(
                escape(str(value)),
                body_style,
            ),
        ]
        for label, value in details
    ]

    table = Table(
        rows,
        colWidths=[52 * mm, 118 * mm],
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CREAM),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, -1), (-1, -1), 1, GOLD),
        ])
    )

    story.append(table)
    story.append(Spacer(1, 10 * mm))

    amounts = [
        ["ORDER TOTAL", money(order.total)],
        ["PAYMENT RECEIVED", money(payment.amount)],
        ["BALANCE AFTER PAYMENT", money(balance_after)],
    ]

    amount_table = Table(
        amounts,
        colWidths=[90 * mm, 80 * mm],
    )

    amount_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "ReceiptRegular"),
            ("FONTNAME", (0, 1), (-1, 1), "ReceiptBold"),
            ("BACKGROUND", (0, 1), (-1, 1), BLACK),
            ("TEXTCOLOR", (0, 1), (-1, 1), GOLD),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ])
    )

    story.append(amount_table)
    story.append(Spacer(1, 12 * mm))

    story.append(
        Paragraph(
            "This receipt confirms the payment amount shown "
            "above. Any remaining balance is still payable.",
            body_style,
        )
    )

    story.append(Spacer(1, 12 * mm))

    story.append(
        Paragraph(
            "Thank you for choosing KING'S GRILLZ!",
            center_style,
        )
    )

    doc.build(story)
    buffer.seek(0)

    return buffer

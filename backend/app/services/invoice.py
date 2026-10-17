
from io import BytesIO
from datetime import timezone
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    Image,
)


# KING'S GRILLZ BRAND COLOURS
BLACK = colors.HexColor("#171717")
GOLD = colors.HexColor("#D9A441")
ORANGE = colors.HexColor("#E66B24")
CREAM = colors.HexColor("#FAF7F0")
GREY = colors.HexColor("#666666")
WHITE = colors.white


# REGISTER UNICODE FONTS
def setup_fonts():
    font_locations = [
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]

    for regular, bold in font_locations:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(
                TTFont("KGRegular", str(regular))
            )
            pdfmetrics.registerFont(
                TTFont("KGBold", str(bold))
            )
            return "KGRegular", "KGBold"

    raise RuntimeError(
        "A Unicode font was not found. "
        "Install Arial or DejaVu Sans to generate invoices."
    )


FONT, FONT_BOLD = setup_fonts()


def naira(amount):
    return f"₦{amount:,.2f}"


def safe(value):
    if value is None or value == "":
        return "—"
    return escape(str(value))


def generate_invoice(order, customer, product):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"KING'S GRILLZ Invoice {order.order_number}",
        author="KING'S GRILLZ",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="KGBrand",
            fontName=FONT_BOLD,
            fontSize=25,
            leading=32,
            textColor=GOLD,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KGTagline",
            fontName=FONT_BOLD,
            fontSize=9,
            leading=15,
            textColor=BLACK,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KGSmall",
            fontName=FONT,
            fontSize=8.5,
            leading=14,
            textColor=GREY,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KGHeading",
            fontName=FONT_BOLD,
            fontSize=13,
            leading=19,
            textColor=BLACK,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KGBody",
            fontName=FONT,
            fontSize=9,
            leading=15,
            textColor=BLACK,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KGCell",
            fontName=FONT,
            fontSize=8,
            leading=12,
            textColor=BLACK,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KGCellWhite",
            fontName=FONT_BOLD,
            fontSize=8,
            leading=12,
            textColor=WHITE,
        )
    )

    styles.add(
        ParagraphStyle(
            name="KGFooter",
            fontName=FONT,
            fontSize=8,
            leading=14,
            alignment=TA_CENTER,
            textColor=GREY,
        )
    )

    def paragraph(value, style="KGBody"):
        return Paragraph(safe(value), styles[style])

    story = []
    logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        story.append(Image(str(logo_path), width=40*mm, height=40*mm, hAlign="CENTER"))
        story.append(Spacer(1, 6*mm))


    # HEADER
    story.append(
        Paragraph("KING'S GRILLZ", styles["KGBrand"])
    )
    story.append(
        Paragraph(
            "YOUR PREMIUM AWO PLUG",
            styles["KGTagline"],
        )
    )
    story.append(
        Paragraph(
            "33 Kayode Arikawe Street",
            styles["KGSmall"],
        )
    )
    story.append(
        Paragraph(
            "WhatsApp: 08142966975 | Instagram: @kingsgrillz_",
            styles["KGSmall"],
        )
    )

    story.append(Spacer(1, 10 * mm))

    # INVOICE HEADING
    story.append(
        Paragraph("ORDER INVOICE", styles["KGHeading"])
    )
    story.append(Spacer(1, 5 * mm))

    created = order.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    lagos_time = created.astimezone(
        ZoneInfo("Africa/Lagos")
    )

    details = [
        ["Invoice Reference", safe(order.order_number)],
        [
            "Date",
            lagos_time.strftime("%d %B %Y, %I:%M %p"),
        ],
        ["Customer", safe(customer.name)],
        ["Phone", safe(customer.phone)],
        ["Preparation", safe(order.preparation)],
        ["Fulfilment", safe(order.fulfilment)],
        [
            "Payment Status",
            safe(order.payment_status).upper(),
        ],
        [
            "Order Status",
            safe(order.order_status).upper(),
        ],
    ]

    if order.fulfilment == "Delivery":
        details.append(
            ["Delivery Provider", safe(order.delivery_provider)]
        )
        details.append(
            ["Delivery Address", safe(order.delivery_address)]
        )

    details_table = Table(
        [
            [
                paragraph(label, "KGCell"),
                paragraph(value, "KGCell"),
            ]
            for label, value in details
        ],
        colWidths=[47 * mm, 117 * mm],
        hAlign="LEFT",
    )

    details_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), CREAM),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            (
                "LINEBELOW",
                (0, -1),
                (-1, -1),
                0.7,
                GOLD,
            ),
        ])
    )

    story.append(details_table)
    story.append(Spacer(1, 9 * mm))

    # ORDER ITEMS
    item_rows = [
        [
            paragraph("ITEM", "KGCellWhite"),
            paragraph("QTY", "KGCellWhite"),
            paragraph("UNIT PRICE", "KGCellWhite"),
            paragraph("AMOUNT", "KGCellWhite"),
        ],
        [
            paragraph(product.name, "KGCell"),
            paragraph(order.quantity, "KGCell"),
            paragraph(naira(order.unit_price), "KGCell"),
            paragraph(naira(order.subtotal), "KGCell"),
        ],
    ]

    item_table = Table(
        item_rows,
        colWidths=[64 * mm, 14 * mm, 42 * mm, 44 * mm],
        hAlign="LEFT",
    )

    item_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLACK),
            ("BACKGROUND", (0, 1), (-1, 1), CREAM),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ])
    )

    story.append(item_table)
    story.append(Spacer(1, 7 * mm))

    # TOTALS
    totals = [
        ["Subtotal", naira(order.subtotal)],
        ["Delivery Fee", naira(order.delivery_fee)],
        ["TOTAL", naira(order.total)],
        ["Amount Paid", naira(order.amount_paid)],
        [
            "Balance Due",
            naira(order.total - order.amount_paid),
        ],
    ]

    totals_table = Table(
        totals,
        colWidths=[99 * mm, 65 * mm],
        hAlign="RIGHT",
    )

    totals_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), FONT),
            ("FONTNAME", (0, 2), (-1, 2), FONT_BOLD),
            ("FONTNAME", (0, 4), (-1, 4), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BACKGROUND", (0, 2), (-1, 2), BLACK),
            ("TEXTCOLOR", (0, 2), (-1, 2), GOLD),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            (
                "LINEBELOW",
                (0, 4),
                (-1, 4),
                1,
                GOLD,
            ),
        ])
    )

    story.append(totals_table)
    story.append(Spacer(1, 9 * mm))

    # PAYMENT INSTRUCTIONS
    payment_section = [
        Paragraph(
            "PAYMENT DETAILS",
            styles["KGHeading"],
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "<b>Bank:</b> PalmPay",
            styles["KGBody"],
        ),
        Paragraph(
            "<b>Account Name:</b> Kings Grillz Ventures",
            styles["KGBody"],
        ),
        Paragraph(
            "<b>Account Number:</b> 9552604707",
            styles["KGBody"],
        ),
    ]

    story.append(KeepTogether(payment_section))
    story.append(Spacer(1, 10 * mm))

    # FOOTER
    story.append(
        Paragraph(
            "Thank you for choosing KING'S GRILLZ!",
            styles["KGTagline"],
        )
    )
    story.append(
        Paragraph(
            "Freshly prepared. Premium taste.",
            styles["KGFooter"],
        )
    )
    story.append(
        Paragraph(
            "This invoice is not proof of payment. "
            "An official receipt is issued after payment confirmation.",
            styles["KGFooter"],
        )
    )

    document.build(story)
    buffer.seek(0)

    return buffer

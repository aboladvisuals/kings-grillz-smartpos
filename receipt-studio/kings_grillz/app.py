"""Premium offline desktop interface for KING'S GRILLZ Receipt Studio."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .database import (
    Document,
    Settings,
    backup_database,
    list_documents,
    load_settings,
    mark_paid,
    restore_database,
    save_document,
    save_settings,
)
from .paths import export_dir, logo_path
from .pdf import naira, write_pdf
from .png import write_png
from .share import open_folder, open_whatsapp


STYLE = """
QMainWindow, QWidget { background: #FAF7F0; color: #171717; font-size: 14px; }
QFrame#sidebar { background: #171717; }
QLabel#brand { color: #D9A441; font-size: 18px; font-weight: 700; }
QLabel#tag { color: #FAF7F0; font-size: 11px; }
QPushButton.nav { background: transparent; color: #FAF7F0; text-align: left; padding: 10px 16px; border: none; }
QPushButton.nav:checked { background: #D9A441; color: #171717; font-weight: 700; }
QPushButton { background: #D9A441; color: #171717; border: none; padding: 8px 14px; font-weight: 600; border-radius: 4px; }
QPushButton:hover { background: #E66B24; color: white; }
QLineEdit, QSpinBox, QComboBox, QTextEdit { background: white; border: 1px solid #D9A441; padding: 6px; border-radius: 4px; }
QTableWidget { background: white; border: 1px solid #D9A441; }
QHeaderView::section { background: #171717; color: #D9A441; padding: 6px; }
"""


class Studio(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("KING'S GRILLZ Receipt Studio")
        self.resize(1100, 720)
        logo = logo_path()
        if logo.exists():
            self.setWindowIcon(QIcon(str(logo)))
        self.settings = load_settings()
        self._build()
        self.refresh_history()

    def _build(self) -> None:
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12, 18, 12, 18)
        if logo_path().exists():
            mark = QLabel()
            pix = QPixmap(str(logo_path())).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            mark.setPixmap(pix)
            mark.setAlignment(Qt.AlignCenter)
            side.addWidget(mark)
        brand = QLabel("KING'S GRILLZ")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignCenter)
        tag = QLabel("RECEIPT STUDIO")
        tag.setObjectName("tag")
        tag.setAlignment(Qt.AlignCenter)
        side.addWidget(brand)
        side.addWidget(tag)
        side.addSpacing(16)

        self.stack = QStackedWidget()
        self.nav_buttons = []
        for index, label in enumerate(("New document", "History", "Settings")):
            button = QPushButton(label)
            button.setProperty("class", "nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, i=index: self.show_page(i))
            side.addWidget(button)
            self.nav_buttons.append(button)
        side.addStretch()
        offline = QLabel("Offline · no login required")
        offline.setObjectName("tag")
        offline.setAlignment(Qt.AlignCenter)
        side.addWidget(offline)
        layout.addWidget(sidebar)

        self.stack.addWidget(self._create_page())
        self.stack.addWidget(self._history_page())
        self.stack.addWidget(self._settings_page())
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.show_page(0)

    def show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

    def _create_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Create invoice or receipt")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #171717;")
        layout.addWidget(title)
        hint = QLabel("Invoices stay unpaid until you explicitly mark them paid.")
        hint.setStyleSheet("color: #666;")
        layout.addWidget(hint)

        form = QFormLayout()
        self.name = QLineEdit()
        self.phone = QLineEdit()
        self.product = QLineEdit(self.settings.product_name)
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 999)
        self.quantity.setValue(1)
        self.price = QSpinBox()
        self.price.setRange(0, 10_000_000)
        self.price.setValue(self.settings.unit_price)
        self.price.setSuffix(" ₦")
        self.preparation = QComboBox()
        self.preparation.addItems(["Whole", "Chopped"])
        self.fulfilment = QComboBox()
        self.fulfilment.addItems(["Pickup", "Delivery"])
        self.delivery_fee = QSpinBox()
        self.delivery_fee.setRange(0, 1_000_000)
        self.delivery_fee.setValue(self.settings.delivery_fee)
        self.delivery_fee.setSuffix(" ₦")
        self.kind = QComboBox()
        self.kind.addItems(["Invoice (unpaid)", "Receipt (paid)"])
        self.notes = QTextEdit()
        self.notes.setFixedHeight(70)
        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #E66B24;")
        for widget in (self.quantity, self.price, self.delivery_fee, self.fulfilment):
            widget.valueChanged.connect(self.update_total) if hasattr(widget, "valueChanged") else widget.currentTextChanged.connect(self.update_total)
        self.fulfilment.currentTextChanged.connect(self._toggle_delivery)
        form.addRow("Customer name", self.name)
        form.addRow("Phone", self.phone)
        form.addRow("Product", self.product)
        form.addRow("Quantity", self.quantity)
        form.addRow("Unit price", self.price)
        form.addRow("Preparation", self.preparation)
        form.addRow("Fulfilment", self.fulfilment)
        form.addRow("Delivery fee", self.delivery_fee)
        form.addRow("Document", self.kind)
        form.addRow("Notes", self.notes)
        form.addRow("Total", self.total_label)
        layout.addLayout(form)

        actions = QHBoxLayout()
        save_pdf = QPushButton("Save PDF")
        save_png = QPushButton("Save PNG")
        save_as = QPushButton("Save As…")
        share = QPushButton("Share to WhatsApp")
        save_pdf.clicked.connect(lambda: self.create_document("pdf"))
        save_png.clicked.connect(lambda: self.create_document("png"))
        save_as.clicked.connect(self.save_as_new)
        share.clicked.connect(self.create_and_share)
        actions.addWidget(save_pdf)
        actions.addWidget(save_png)
        actions.addWidget(save_as)
        actions.addWidget(share)
        actions.addStretch()
        layout.addLayout(actions)
        tip = QLabel("WhatsApp opens the message. Attach the PDF from the folder that opens — Windows cannot attach it automatically.")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #666;")
        layout.addWidget(tip)
        layout.addStretch()
        self.update_total()
        return page

    def _toggle_delivery(self) -> None:
        is_delivery = self.fulfilment.currentText() == "Delivery"
        self.delivery_fee.setEnabled(is_delivery)
        if not is_delivery:
            self.delivery_fee.setValue(0)
        self.update_total()

    def update_total(self) -> None:
        subtotal = self.quantity.value() * self.price.value()
        fee = self.delivery_fee.value() if self.fulfilment.currentText() == "Delivery" else 0
        self.total_label.setText(naira(subtotal + fee))

    def _payload(self) -> dict:
        name = self.name.text().strip()
        phone = self.phone.text().strip()
        product = self.product.text().strip()
        if not name or not phone or not product:
            raise ValueError("Customer name, phone and product are required.")
        quantity = self.quantity.value()
        unit_price = self.price.value()
        fee = self.delivery_fee.value() if self.fulfilment.currentText() == "Delivery" else 0
        subtotal = quantity * unit_price
        total = subtotal + fee
        paid = self.kind.currentIndex() == 1
        return {
            "kind": "receipt" if paid else "invoice",
            "customer_name": name,
            "customer_phone": phone,
            "product_name": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "preparation": self.preparation.currentText(),
            "fulfilment": self.fulfilment.currentText(),
            "delivery_fee": fee,
            "subtotal": subtotal,
            "total": total,
            "amount_paid": total if paid else 0,
            "payment_status": "paid" if paid else "unpaid",
            "notes": self.notes.toPlainText().strip(),
        }

    def create_document(self, mode: str) -> None:
        try:
            payload = self._payload()
        except ValueError as exc:
            QMessageBox.warning(self, "Missing details", str(exc))
            return
        document = save_document(payload)
        folder = export_dir()
        written = []
        if mode in ("pdf", "both"):
            written.append(write_pdf(document, folder / f"{document.number}.pdf"))
        if mode in ("png", "both"):
            written.append(write_png(document, folder / f"{document.number}.png"))
        QMessageBox.information(
            self,
            "Saved",
            f"{document.number} saved as {document.payment_status.upper()}.\n" + "\n".join(str(p) for p in written),
        )
        self.refresh_history()

    def _history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Receipt history")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        layout.addWidget(title)
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name, phone or number")
        self.search.textChanged.connect(self.refresh_history)
        search_row.addWidget(self.search)
        layout.addLayout(search_row)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Number", "Customer", "Total", "Status", "Date", "Kind"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        for label, handler in (
            ("Reprint PDF", self.reprint_pdf),
            ("Reprint PNG", self.reprint_png),
            ("Save As…", self.save_as_selected),
            ("Share to WhatsApp", self.share_selected),
            ("Mark paid", self.mark_selected_paid),
            ("Backup", self.do_backup),
            ("Restore", self.do_restore),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        return page

    def refresh_history(self) -> None:
        docs = list_documents(self.search.text() if hasattr(self, "search") else "")
        self.table.setRowCount(len(docs))
        for row, doc in enumerate(docs):
            values = [doc.number, doc.customer_name, naira(doc.total), doc.payment_status.upper(), doc.created_at[:16], doc.kind]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
            self.table.item(row, 0).setData(Qt.UserRole, doc.id)

    def _selected(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Select a document", "Choose a row in the history first.")
            return None
        return self.table.item(rows[0].row(), 0).data(Qt.UserRole)

    def _selected_doc(self) -> Document | None:
        doc_id = self._selected()
        if doc_id is None:
            return None
        docs = list_documents()
        return next((doc for doc in docs if doc.id == doc_id), None)

    def save_as_new(self) -> None:
        try:
            payload = self._payload()
        except ValueError as exc:
            QMessageBox.warning(self, "Missing details", str(exc))
            return
        chosen, selected = QFileDialog.getSaveFileName(
            self, "Save receipt", f"{payload['customer_name']}.pdf", "PDF (*.pdf);;PNG (*.png)"
        )
        if not chosen:
            return
        document = save_document(payload)
        path = Path(chosen)
        if path.suffix.lower() == ".png" or "png" in selected.lower():
            write_png(document, path if path.suffix else path.with_suffix(".png"))
        else:
            write_pdf(document, path if path.suffix else path.with_suffix(".pdf"))
        self.refresh_history()
        QMessageBox.information(self, "Saved", f"{document.number} saved to:\n{path}")

    def create_and_share(self) -> None:
        try:
            payload = self._payload()
        except ValueError as exc:
            QMessageBox.warning(self, "Missing details", str(exc))
            return
        document = save_document(payload)
        pdf_path = write_pdf(document, export_dir() / f"{document.number}.pdf")
        self.refresh_history()
        self._share(document, pdf_path)

    def save_as_selected(self) -> None:
        doc = self._selected_doc()
        if not doc:
            return
        chosen, selected = QFileDialog.getSaveFileName(
            self, "Save receipt", f"{doc.number}.pdf", "PDF (*.pdf);;PNG (*.png)"
        )
        if not chosen:
            return
        path = Path(chosen)
        if path.suffix.lower() == ".png" or "png" in selected.lower():
            written = write_png(doc, path if path.suffix else path.with_suffix(".png"))
        else:
            written = write_pdf(doc, path if path.suffix else path.with_suffix(".pdf"))
        QMessageBox.information(self, "Saved", str(written))

    def share_selected(self) -> None:
        doc = self._selected_doc()
        if not doc:
            return
        pdf_path = write_pdf(doc, export_dir() / f"{doc.number}.pdf")
        self._share(doc, pdf_path)

    def _share(self, doc: Document, pdf_path: Path) -> None:
        try:
            open_whatsapp(doc)
        except ValueError as exc:
            QMessageBox.warning(self, "WhatsApp", str(exc))
            return
        open_folder(pdf_path)
        QMessageBox.information(
            self,
            "Attach the PDF",
            f"WhatsApp is opening with {doc.number} and the total.\n\n"
            f"Windows cannot attach the PDF automatically.\n"
            f"The receipt folder is open. Attach this file:\n{pdf_path.name}",
        )

    def reprint_pdf(self) -> None:

        doc = self._selected_doc()
        if not doc:
            return
        path = write_pdf(doc, export_dir() / f"{doc.number}.pdf")
        QMessageBox.information(self, "PDF ready", str(path))

    def reprint_png(self) -> None:
        doc = self._selected_doc()
        if not doc:
            return
        path = write_png(doc, export_dir() / f"{doc.number}.png")
        QMessageBox.information(self, "PNG ready", str(path))

    def mark_selected_paid(self) -> None:
        doc = self._selected_doc()
        if not doc:
            return
        if doc.payment_status == "paid":
            QMessageBox.information(self, "Already paid", f"{doc.number} is already a paid receipt.")
            return
        if QMessageBox.question(self, "Mark paid", f"Mark {doc.number} as paid?") != QMessageBox.Yes:
            return
        mark_paid(doc.id)
        self.refresh_history()

    def do_backup(self) -> None:
        path = backup_database()
        QMessageBox.information(self, "Backup saved", str(path))

    def do_restore(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self, "Restore backup", str(export_dir()), "Database (*.db)")
        if not chosen:
            return
        if QMessageBox.question(self, "Restore", "Replace the current local history with this backup?") != QMessageBox.Yes:
            return
        restore_database(Path(chosen))
        self.settings = load_settings()
        self.refresh_history()
        QMessageBox.information(self, "Restored", "Local history restored.")

    def _settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Business settings")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        layout.addWidget(title)
        form = QFormLayout()
        self.set_product = QLineEdit(self.settings.product_name)
        self.set_price = QSpinBox()
        self.set_price.setRange(0, 10_000_000)
        self.set_price.setValue(self.settings.unit_price)
        self.set_price.setSuffix(" ₦")
        self.set_fee = QSpinBox()
        self.set_fee.setRange(0, 1_000_000)
        self.set_fee.setValue(self.settings.delivery_fee)
        self.set_fee.setSuffix(" ₦")
        self.set_phone = QLineEdit(self.settings.business_phone)
        form.addRow("Default product", self.set_product)
        form.addRow("Default unit price", self.set_price)
        form.addRow("Default delivery fee", self.set_fee)
        form.addRow("Business phone", self.set_phone)
        layout.addLayout(form)
        save = QPushButton("Save settings")
        save.clicked.connect(self.save_business_settings)
        layout.addWidget(save)
        note = QLabel("Settings and history are stored in your application data folder, not inside the installed program.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #666;")
        layout.addWidget(note)
        layout.addStretch()
        return page

    def save_business_settings(self) -> None:
        self.settings = Settings(
            product_name=self.set_product.text().strip() or self.settings.product_name,
            unit_price=self.set_price.value(),
            delivery_fee=self.set_fee.value(),
            business_phone=self.set_phone.text().strip(),
        )
        save_settings(self.settings)
        self.product.setText(self.settings.product_name)
        self.price.setValue(self.settings.unit_price)
        self.delivery_fee.setValue(self.settings.delivery_fee)
        QMessageBox.information(self, "Saved", "Default product and prices updated.")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = Studio()
    window.show()
    sys.exit(app.exec())

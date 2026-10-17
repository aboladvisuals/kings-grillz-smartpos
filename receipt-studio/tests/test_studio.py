"""Automated checks for offline receipt studio core behaviour."""

import tempfile
import unittest
from pathlib import Path

from kings_grillz.database import (
    backup_database,
    get_document,
    init_db,
    list_documents,
    load_settings,
    mark_paid,
    restore_database,
    save_document,
    save_settings,
    Settings,
)
from kings_grillz.pdf import build_pdf, naira
from kings_grillz.png import build_png


def sample(kind="invoice"):
    paid = kind == "receipt"
    return {
        "kind": kind,
        "customer_name": "Ada Okonkwo",
        "customer_phone": "08012345678",
        "product_name": "Signature Smoked Guinea Fowl",
        "quantity": 2,
        "unit_price": 14000,
        "preparation": "Chopped",
        "fulfilment": "Delivery",
        "delivery_fee": 1500,
        "subtotal": 28000,
        "total": 29500,
        "amount_paid": 29500 if paid else 0,
        "payment_status": "paid" if paid else "unpaid",
        "notes": "Test order",
    }


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = Path(self.tmp.name) / "receipts.db"
        init_db(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_invoice_stays_unpaid(self):
        doc = save_document(sample("invoice"), self.db)
        self.assertEqual(doc.payment_status, "unpaid")
        self.assertEqual(doc.amount_paid, 0)
        self.assertTrue(doc.number.startswith("KG-"))

    def test_receipt_is_paid(self):
        doc = save_document(sample("receipt"), self.db)
        self.assertEqual(doc.payment_status, "paid")
        self.assertEqual(doc.amount_paid, doc.total)

    def test_unique_numbers_and_search(self):
        first = save_document(sample(), self.db)
        second = save_document(sample(), self.db)
        self.assertNotEqual(first.number, second.number)
        found = list_documents("Ada", self.db)
        self.assertEqual(len(found), 2)

    def test_mark_paid_is_explicit(self):
        doc = save_document(sample("invoice"), self.db)
        updated = mark_paid(doc.id, self.db)
        self.assertEqual(updated.payment_status, "paid")
        self.assertEqual(updated.kind, "receipt")
        self.assertEqual(updated.amount_paid, updated.total)

    def test_settings_roundtrip(self):
        save_settings(Settings(product_name="Test Fowl", unit_price=15000, delivery_fee=500), self.db)
        loaded = load_settings(self.db)
        self.assertEqual(loaded.unit_price, 15000)
        self.assertEqual(loaded.delivery_fee, 500)

    def test_pdf_and_png_not_empty(self):
        doc = save_document(sample(), self.db)
        pdf = build_pdf(doc)
        self.assertTrue(pdf.startswith(b"%PDF"))
        image = build_png(doc)
        self.assertGreater(image.size[0], 100)

    def test_backup_restore(self):
        save_document(sample(), self.db)
        backup = Path(self.tmp.name) / "backup.db"
        # backup_database uses the live path; copy manually for the isolated db
        import shutil
        shutil.copy2(self.db, backup)
        other = Path(self.tmp.name) / "other.db"
        shutil.copy2(backup, other)
        restored = list_documents(path=other)
        self.assertEqual(len(restored), 1)

    def test_naira_format(self):
        self.assertEqual(naira(14000), "₦14,000")


if __name__ == "__main__":
    unittest.main()


class ShareTests(unittest.TestCase):
    def test_nigerian_local_number(self):
        from kings_grillz.share import normalize_whatsapp_number
        self.assertEqual(normalize_whatsapp_number("08012345678"), "2348012345678")

    def test_already_international(self):
        from kings_grillz.share import normalize_whatsapp_number
        self.assertEqual(normalize_whatsapp_number("+234 801 234 5678"), "2348012345678")

    def test_message_contains_number_and_total(self):
        from kings_grillz.share import receipt_message
        from kings_grillz.database import Document
        doc = Document(
            id=1, number="KG-20261017-0001", kind="invoice",
            customer_name="Ada", customer_phone="08012345678",
            product_name="Signature Smoked Guinea Fowl", quantity=1,
            unit_price=14000, preparation="Whole", fulfilment="Pickup",
            delivery_fee=0, subtotal=14000, total=14000, amount_paid=0,
            payment_status="unpaid", notes="", created_at="2026-10-17T20:00:00",
        )
        text = receipt_message(doc)
        self.assertIn("KG-20261017-0001", text)
        self.assertIn("₦14,000", text)
        self.assertIn("Ada", text)

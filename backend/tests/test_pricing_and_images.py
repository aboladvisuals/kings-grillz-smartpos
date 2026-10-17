"""Regression tests for editable pricing, historical prices, and image generation.

Run: python -m unittest discover -s tests -v
Uses the isolated in-memory SQLite harness from test_order_status.
"""
import json
import asyncio

from test_order_status import SupportCase, request


class PricingAndImageTests(SupportCase):
    def test_admin_can_update_product_price(self):
        admin_headers = self.session_headers(1)  # admin
        self.headers = admin_headers
        status, body = self.call("PATCH", "/api/products/1/price", {"price": 15000})
        self.assertEqual(status, 200)
        self.assertEqual(body["price"], 15000)
        self.assertEqual(body["old_price"], 10000)

    def test_cashier_cannot_update_catalogue_price(self):
        cashier_headers = self.session_headers(2)  # cashier
        self.headers = cashier_headers
        status, body = self.call("PATCH", "/api/products/1/price", {"price": 15000})
        self.assertEqual(status, 403)

    def test_custom_unit_price_is_stored_and_historical(self):
        status, body = self.call("POST", "/api/orders", {
            "customer_name": "Test Customer",
            "customer_phone": "08012345678",
            "product_id": 1,
            "quantity": 2,
            "preparation": "Whole",
            "fulfilment": "Pickup",
            "unit_price": 12000,
        })
        self.assertEqual(status, 201)
        self.assertEqual(body["unit_price"], 12000)
        self.assertEqual(body["subtotal"], 24000)

        # Change catalogue price; existing order must keep 12000
        admin_headers = self.session_headers(1)
        self.headers = admin_headers
        self.call("PATCH", "/api/products/1/price", {"price": 16000})

        status, order = self.call("GET", f"/api/orders/{body['order_id']}")
        self.assertEqual(order["unit_price"], 12000)
        self.assertEqual(order["subtotal"], 24000)

    def test_delivery_fee_editable_and_zero_allowed(self):
        status, body = self.call("POST", "/api/orders", {
            "customer_name": "Test Customer",
            "customer_phone": "08012345678",
            "product_id": 1,
            "quantity": 1,
            "preparation": "Whole",
            "fulfilment": "Delivery",
            "delivery_provider": "inDrive",
            "delivery_address": "123 Test Street",
            "delivery_fee": 0,
        })
        self.assertEqual(status, 201)
        self.assertEqual(body["delivery_fee"], 0)
        self.assertEqual(body["total"], body["subtotal"])

    def test_invoice_png_endpoint_returns_png(self):
        status, order = self.call("POST", "/api/orders", {
            "customer_name": "Test Customer",
            "customer_phone": "08012345678",
            "product_id": 1,
            "quantity": 1,
            "preparation": "Whole",
            "fulfilment": "Pickup",
        })
        self.assertEqual(status, 201)
        # Direct ASGI call for binary
        st, content, headers = asyncio.run(request(
            "GET", f"/api/orders/{order['order_id']}/invoice.png",
            None, self.headers, True
        ))
        self.assertEqual(st, 200)
        self.assertIn("image/png", headers.get("content-type", ""))
        self.assertTrue(content.startswith(b"\x89PNG"))

    def test_negative_price_rejected(self):
        admin_headers = self.session_headers(1)
        self.headers = admin_headers
        status, body = self.call("PATCH", "/api/products/1/price", {"price": -1})
        self.assertIn(status, (400, 422))

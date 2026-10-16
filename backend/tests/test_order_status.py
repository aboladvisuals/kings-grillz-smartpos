"""Run: .venv/Scripts/python -m unittest discover -s tests -v.

Exercises the actual ASGI routes against an isolated in-memory database.
"""
import asyncio
import json
import unittest
import secrets
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from app.security import Staff, StaffSession, hash_password, token_hash


async def request(method, path, payload=None, headers=None, return_headers=False, scheme="http"):
    body = json.dumps(payload).encode() if payload is not None else b""
    messages = []
    sent = False

    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        await asyncio.Event().wait()

    async def send(message):
        messages.append(message)

    await app({
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1", "method": method, "scheme": scheme,
        "path": path, "raw_path": path.encode(), "query_string": b"",
        "root_path": "", "headers": [(key.encode(), value.encode()) for key, value in {
            "host": "localhost", "content-type": "application/json", **(headers or {})
        }.items()],
        "client": ("127.0.0.1", 1), "server": ("localhost", 80),
    }, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    content = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    if return_headers:
        response_headers = next(m["headers"] for m in messages if m["type"] == "http.response.start")
        return status, content, {key.decode(): value.decode() for key, value in response_headers}
    return status, content


class SupportCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = secrets.token_urlsafe(24)
        cls.password_hash = hash_password(cls.password)

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([
            Customer(id=1, name="Test Customer", phone="08012345678"),
            Product(id=1, name="Test Grill", price=10000, currency="NGN", available=True),
        ])
        self.db.commit()

        for index, role in enumerate(("admin", "cashier", "operations"), start=1):
            self.db.add(Staff(id=index, username=role, password_hash=self.password_hash, role=role, active=True))
        self.db.commit()
        self.headers = self.session_headers(1)

        def override_db():
            yield self.db
        app.dependency_overrides[get_db] = override_db

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def call(self, method, path, payload=None):
        status, body = asyncio.run(request(method, path, payload, self.headers))
        return status, json.loads(body)

    def session_headers(self, staff_id):
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        now = int(time.time())
        self.db.add(StaffSession(token_hash=token_hash(token), staff_id=staff_id, csrf_token=csrf,
                                 expires_at=now + 28800, last_seen=now))
        self.db.commit()
        return {"cookie": "kg_session=" + token, "origin": "http://localhost:5173", "x-csrf-token": csrf}

    def order(self, fulfilment="Pickup"):
        status, result = self.call("POST", "/api/orders", {
            "customer_name": "Test Customer", "customer_phone": "08012345678",
            "quantity": 1, "preparation": "Whole", "fulfilment": fulfilment,
            "delivery_provider": "Company Rider" if fulfilment == "Delivery" else None,
            "delivery_address": "Test address" if fulfilment == "Delivery" else None,
        })
        self.assertEqual(status, 201)
        return result["order_id"]

class OrderStatusTests(SupportCase):
    def test_all_transitions_for_both_fulfilment_types(self):
        transitions = {
            "pending": ["preparing", "cancelled"], "preparing": ["ready", "cancelled"],
            "ready": ["dispatched", "completed", "cancelled"],
            "dispatched": ["completed"], "completed": [], "cancelled": [],
        }
        for fulfilment in ("Pickup", "Delivery"):
            order_id = self.order(fulfilment)
            for previous in transitions:
                for target in transitions:
                    with self.subTest(fulfilment=fulfilment, previous=previous, target=target):
                        order = self.db.get(Order, order_id)
                        order.order_status = previous
                        self.db.commit()
                        valid = target in transitions[previous] and not (target == "dispatched" and fulfilment == "Pickup")
                        status, result = self.call("PATCH", f"/api/orders/{order_id}/status", {"order_status": target})
                        self.assertEqual(status, 200 if valid else 400)
                        if valid:
                            self.assertEqual(set(result), {"message", "order_number", "previous_status", "order_status", "payment_status", "balance"})
                            self.assertEqual(result["previous_status"], previous)
                            self.assertEqual(result["order_status"], target)
                            self.assertEqual(result["payment_status"], "unpaid")
                            self.assertEqual(result["balance"], 10000)
                        else:
                            self.assertIsInstance(result["detail"], str)
                        _, details = self.call("GET", f"/api/orders/{order_id}")
                        self.assertEqual(details["order_status"], target if valid else previous)

    def test_schema_and_invalid_requests(self):
        _, schema = self.call("GET", "/openapi.json")
        operation = schema["paths"]["/api/orders/{order_id}/status"]["patch"]
        self.assertEqual(operation["requestBody"]["content"]["application/json"]["schema"]["$ref"], "#/components/schemas/OrderStatusUpdate")
        self.assertEqual(schema["components"]["schemas"]["OrderStatusUpdate"]["required"], ["order_status"])
        order_id = self.order()
        for payload in ({"status": "ready"}, {"order_status": "unknown"}, {}):
            self.assertEqual(self.call("PATCH", f"/api/orders/{order_id}/status", payload)[0], 422)
        self.assertEqual(self.call("PATCH", "/api/orders/99999/status", {"order_status": "ready"})[0], 404)

    def test_payment_invoice_and_receipt_survive_status_changes(self):
        order_id = self.order("Delivery")
        status, payment = self.call("POST", f"/api/orders/{order_id}/payments", {"amount": 4000, "method": "Cash", "reference": "STATUS-TEST"})
        self.assertEqual(status, 201)
        for target in ("preparing", "ready", "dispatched", "completed"):
            status, result = self.call("PATCH", f"/api/orders/{order_id}/status", {"order_status": target})
            self.assertEqual(status, 200)
            self.assertEqual(result["balance"], 6000)
            self.assertEqual(result["payment_status"], "partially_paid")
        _, history = self.call("GET", f"/api/orders/{order_id}/payments")
        self.assertEqual(history["payments"][0]["payment_id"], payment["payment_id"])
        self.assertEqual(history["amount_paid"], 4000)
        for path in (f"/api/orders/{order_id}/invoice", f"/api/payments/{payment['payment_id']}/receipt"):
            status, content = asyncio.run(request("GET", path, headers=self.headers))
            self.assertEqual(status, 200)
            self.assertTrue(content.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()

from urllib.parse import quote
from fastapi import Depends, FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.database import engine
from app.security import Staff, audit, initialize_security, require_staff, require_payment_staff, settings
from app.auth import router as auth_router
from app.security_middleware import SecurityHeaders
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from app.services.receipt import generate_receipt
from app.database import get_db
from app.models.product import Product
from typing import Literal

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import status
from sqlalchemy import select, update, case

from app.models.customer import Customer
from app.models.order import Order
from app.schemas.order import OrderCreate

from fastapi.responses import StreamingResponse
from app.services.invoice import generate_invoice
from sqlalchemy.exc import IntegrityError
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate
@asynccontextmanager
async def lifespan(app):
    initialize_security(engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    dependencies=[Depends(require_staff)],
    docs_url=None, redoc_url=None, openapi_url=None,
    title="KING'S GRILLZ SmartPOS API",
    description="Order, invoice and receipt management system",
    version="1.0.0",
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings().hosts))
app.add_middleware(SecurityHeaders)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Pydantic's default errors include raw input, potentially including passwords.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]})


@app.get("/openapi.json", include_in_schema=False)
def protected_schema(staff: Staff = Depends(require_staff)):
    if staff.role != "admin":
        raise HTTPException(403, "Administrator access required")
    return app.openapi()


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: int
    currency: str
    available: bool
    preparation_options: list[str] = ["Whole", "Chopped"]


@app.get("/")
def home():
    return {
        "business": "KING'S GRILLZ",
        "system": "SmartPOS",
        "status": "running",
        "currency": "NGN",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id).all()


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


@app.post("/api/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_staff),
):
    product = db.get(Product, payload.product_id)

    if product is None or not product.available:
        raise HTTPException(
            status_code=404,
            detail="Product unavailable",
        )

    customer = db.scalar(
        select(Customer).where(
            Customer.phone == payload.customer_phone.strip()
        )
    )

    if customer is None:
        customer = Customer(
            name=payload.customer_name.strip(),
            phone=payload.customer_phone.strip(),
        )
        db.add(customer)
        db.flush()

    subtotal = product.price * payload.quantity
    total = subtotal + payload.delivery_fee

    order = Order(
        order_number="PENDING",
        customer_id=customer.id,
        product_id=product.id,
        quantity=payload.quantity,
        unit_price=product.price,
        preparation=payload.preparation,
        fulfilment=payload.fulfilment,
        delivery_provider=payload.delivery_provider,
        delivery_address=payload.delivery_address,
        delivery_fee=payload.delivery_fee,
        subtotal=subtotal,
        total=total,
        amount_paid=0,
        payment_status="unpaid",
        order_status="pending",
    )

    db.add(order)
    db.flush()

    lagos_date = datetime.now(
        ZoneInfo("Africa/Lagos")
    ).strftime("%Y%m%d")

    order.order_number = (
        f"KG-{lagos_date}-{order.id:05d}"
    )

    audit(db, staff.id, "order_created", order.id)
    db.commit()
    db.refresh(order)

    return {
        "message": "Order created successfully",
        "order_id": order.id,
        "order_number": order.order_number,
        "customer": customer.name,
        "quantity": order.quantity,
        "unit_price": order.unit_price,
        "subtotal": order.subtotal,
        "delivery_fee": order.delivery_fee,
        "total": order.total,
        "payment_status": order.payment_status,
        "order_status": order.order_status,
    }


@app.get("/api/orders")
def get_orders(db: Session = Depends(get_db)):
    orders = db.scalars(
        select(Order).order_by(Order.id.desc())
    ).all()

    return [
        {
            "id": order.id,
            "order_number": order.order_number,
            "customer_id": order.customer_id,
            "quantity": order.quantity,
            "preparation": order.preparation,
            "fulfilment": order.fulfilment,
            "subtotal": order.subtotal,
            "delivery_fee": order.delivery_fee,
            "total": order.total,
            "amount_paid": order.amount_paid,
            "balance": order.total - order.amount_paid,
            "payment_status": order.payment_status,
            "order_status": order.order_status,
            "created_at": order.created_at,
        }
        for order in orders
    ]


@app.get("/api/orders/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    customer = db.get(Customer, order.customer_id)

    return {
        "order_number": order.order_number,
        "customer_name": customer.name,
        "customer_phone": customer.phone,
        "quantity": order.quantity,
        "unit_price": order.unit_price,
        "preparation": order.preparation,
        "fulfilment": order.fulfilment,
        "delivery_provider": order.delivery_provider,
        "delivery_address": order.delivery_address,
        "subtotal": order.subtotal,
        "delivery_fee": order.delivery_fee,
        "total": order.total,
        "amount_paid": order.amount_paid,
        "balance": order.total - order.amount_paid,
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "created_at": order.created_at,
    }


@app.get("/api/orders/{order_id}/invoice")
def download_invoice(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    customer = db.get(Customer, order.customer_id)
    product = db.get(Product, order.product_id)

    if customer is None or product is None:
        raise HTTPException(
            status_code=404,
            detail="Order details not found",
        )

    pdf = generate_invoice(order, customer, product)

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{order.order_number}.pdf"'
        },
    )


@app.get("/api/orders/{order_id}/whatsapp")
def share_order_whatsapp(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    customer = db.get(Customer, order.customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    phone = "".join(
        character
        for character in customer.phone
        if character.isdigit()
    )

    if phone.startswith("0") and len(phone) == 11:
        phone = "234" + phone[1:]
    elif phone.startswith("234") and len(phone) == 13:
        pass
    else:
        raise HTTPException(
            status_code=400,
            detail="Customer must have a valid Nigerian phone number",
        )

    message = (
        f"Hello {customer.name},\n\n"
        f"Thank you for choosing KING'S GRILLZ! 🔥\n\n"
        f"Your order invoice is ready.\n\n"
        f"Order: {order.order_number}\n"
        f"Quantity: {order.quantity}\n"
        f"Total: ₦{order.total:,.2f}\n"
        f"Amount Paid: ₦{order.amount_paid:,.2f}\n"
        f"Balance: ₦{order.total - order.amount_paid:,.2f}\n"
        f"Payment Status: {order.payment_status.upper()}\n\n"
        f"Payment Details:\n"
        f"PalmPay\n"
        f"Kings Grillz Ventures\n"
        f"9552604707\n\n"
        f"Your invoice PDF will be attached separately.\n\n"
        f"KING'S GRILLZ — Your Premium Awo Plug"
    )

    whatsapp_url = (
        f"https://wa.me/{phone}?text={quote(message)}"
    )

    return {
        "order_number": order.order_number,
        "customer": customer.name,
        "whatsapp_url": whatsapp_url,
        "invoice_url": f"/api/orders/{order.id}/invoice",
        "instructions": (
            "Download the invoice PDF, open the WhatsApp link, "
            "and attach the PDF before sending."
        ),
    }


@app.post(
    "/api/orders/{order_id}/payments",
    status_code=status.HTTP_201_CREATED,
)
def record_payment(
    order_id: int,
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_payment_staff),
):
    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    reference = payload.reference.strip()

    if not reference:
        raise HTTPException(
            status_code=422,
            detail="Payment reference is required",
        )

    existing_payment = db.scalar(
        select(Payment).where(
            Payment.reference == reference
        )
    )

    if existing_payment:
        raise HTTPException(
            status_code=409,
            detail="Payment reference already recorded",
        )

    balance = order.total - order.amount_paid

    if balance <= 0:
        raise HTTPException(
            status_code=400,
            detail="Order is already fully paid",
        )

    if payload.amount > balance:
        raise HTTPException(
            status_code=400,
            detail=f"Payment exceeds balance of NGN {balance:,}",
        )

    payment = Payment(
        order_id=order.id,
        amount=payload.amount,
        method=payload.method,
        reference=reference,
        status="confirmed",
    )

    # Atomic balance update prevents concurrent authorized payments exceeding total.
    new_paid = Order.amount_paid + payload.amount
    changed = db.execute(update(Order).where(
        Order.id == order_id, Order.total - Order.amount_paid >= payload.amount,
    ).values(amount_paid=new_paid, payment_status=case(
        (new_paid == Order.total, "paid"), else_="partially_paid",
    )), execution_options={"synchronize_session": False})
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Order balance changed. Refresh before recording payment")
    db.add(payment)

    try:
        db.flush()
        audit(db, staff.id, "payment_recorded", payment.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Duplicate payment reference",
        )

    db.refresh(payment)
    db.refresh(order)

    return {
        "message": "Payment recorded successfully",
        "payment_id": payment.id,
        "order_number": order.order_number,
        "amount_received": payment.amount,
        "method": payment.method,
        "reference": payment.reference,
        "total": order.total,
        "amount_paid": order.amount_paid,
        "balance": order.total - order.amount_paid,
        "payment_status": order.payment_status,
        "order_status": order.order_status,
    }

@app.get("/api/orders/{order_id}/payments")
def get_order_payments(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    payments = db.scalars(
        select(Payment)
        .where(Payment.order_id == order_id)
        .order_by(Payment.id.desc())
    ).all()

    return {
        "order_number": order.order_number,
        "total": order.total,
        "amount_paid": order.amount_paid,
        "balance": order.total - order.amount_paid,
        "payment_status": order.payment_status,
        "payments": [
            {
                "payment_id": payment.id,
                "amount": payment.amount,
                "method": payment.method,
                "reference": payment.reference,
                "status": payment.status,
                "created_at": payment.created_at,
            }
            for payment in payments
        ],
    }

@app.get("/api/payments/{payment_id}/receipt")
def download_payment_receipt(
    payment_id: int,
    db: Session = Depends(get_db),
):
    payment = db.get(Payment, payment_id)

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if payment.status != "confirmed":
        raise HTTPException(
            status_code=400,
            detail="Receipt unavailable for unconfirmed payment",
        )

    order = db.get(Order, payment.order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    customer = db.get(Customer, order.customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    # Calculate the balance immediately after this payment.
    confirmed_payments = db.scalars(
        select(Payment).where(
            Payment.order_id == order.id,
            Payment.status == "confirmed",
            Payment.id <= payment.id,
        )
    ).all()

    total_paid_at_that_point = sum(
        item.amount for item in confirmed_payments
    )

    payment._balance_after = (
        order.total - total_paid_at_that_point
    )

    pdf = generate_receipt(payment, order, customer)

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="KG-R-{payment.id:05d}.pdf"'
        },
    )

class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_status: Literal[
        "pending",
        "preparing",
        "ready",
        "dispatched",
        "completed",
        "cancelled",
    ]


@app.patch("/api/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_staff),
):
    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    current_status = order.order_status
    new_status = payload.order_status

    allowed_transitions = {
        "pending": ["preparing", "cancelled"],
        "preparing": ["ready", "cancelled"],
        "ready": ["dispatched", "completed", "cancelled"],
        "dispatched": ["completed"],
        "completed": [],
        "cancelled": [],
    }

    if new_status not in allowed_transitions.get(
        current_status, []
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot change order from "
                f"'{current_status}' to '{new_status}'"
            ),
        )

    if new_status == "dispatched" and order.fulfilment != "Delivery":
        raise HTTPException(
            status_code=400,
            detail="Pickup orders cannot be dispatched",
        )

    changed = db.execute(update(Order).where(
        Order.id == order_id, Order.order_status == current_status,
    ).values(order_status=new_status), execution_options={"synchronize_session": False})
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Order status changed. Refresh and try again")
    audit(db, staff.id, "order_status_" + new_status, order.id)
    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated successfully",
        "order_number": order.order_number,
        "previous_status": current_status,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "balance": order.total - order.amount_paid,
    }


from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    order_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    unit_price: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    preparation: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    fulfilment: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    delivery_provider: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    delivery_address: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    delivery_fee: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    subtotal: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    total: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    amount_paid: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    payment_status: Mapped[str] = mapped_column(
        String(20), default="unpaid"
    )

    order_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

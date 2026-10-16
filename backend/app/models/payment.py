
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    amount = Column(Integer, nullable=False)

    method = Column(String(30), nullable=False)

    reference = Column(String(100), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="confirmed",
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "reference",
            name="uq_payment_reference",
        ),
    )

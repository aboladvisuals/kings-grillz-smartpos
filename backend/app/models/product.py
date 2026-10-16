
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    price: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="NGN"
    )

    available: Mapped[bool] = mapped_column(
        Boolean, default=True
    )

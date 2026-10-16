
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )

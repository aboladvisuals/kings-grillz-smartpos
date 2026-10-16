
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models.product import Product

from app.models.customer import Customer
from app.models.order import Order
from app.models.payment import Payment

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    existing_product = db.scalar(
        select(Product).where(Product.id == 1)
    )

    if existing_product is None:
        db.add(
            Product(
                id=1,
                name="Signature Smoked Guinea Fowl",
                price=14000,
                currency="NGN",
                available=True,
            )
        )
        db.commit()
        print("Initial guinea fowl product created.")
    else:
        print("Initial product already exists.")

print("KING'S GRILLZ DATABASE READY")

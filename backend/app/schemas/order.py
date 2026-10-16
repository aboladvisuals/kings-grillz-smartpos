
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    customer_name: str = Field(min_length=1, max_length=150)
    customer_phone: str = Field(min_length=7, max_length=20)

    product_id: int = Field(default=1, ge=1, le=2147483647, strict=True)
    quantity: int = Field(ge=1, le=100, strict=True)

    preparation: Literal["Whole", "Chopped"]
    fulfilment: Literal["Pickup", "Delivery"]

    delivery_provider: Literal[
        "inDrive", "Company Rider"
    ] | None = None

    delivery_address: str | None = Field(default=None, max_length=255)
    delivery_fee: int = Field(default=0, ge=0, le=1000000000, strict=True)

    @model_validator(mode="after")
    def validate_delivery(self):
        if self.fulfilment == "Delivery":
            if not self.delivery_provider:
                raise ValueError("Delivery provider is required")
            if not self.delivery_address or not self.delivery_address.strip():
                raise ValueError("Delivery address is required")
        else:
            self.delivery_provider = None
            self.delivery_address = None
            self.delivery_fee = 0

        return self

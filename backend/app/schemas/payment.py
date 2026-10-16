
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    amount: int = Field(gt=0, le=1000000000, strict=True)
    method: Literal[
        "Bank Transfer",
        "PalmPay",
        "Cash",
        "POS",
    ]
    reference: str = Field(min_length=3, max_length=100)

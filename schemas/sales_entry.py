from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateSalesEntry(BaseModel):
    quotation_sent_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    po_received_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    po_expected_tomorrow_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    po_expected_this_week_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)

    model_config = ConfigDict(extra="forbid")

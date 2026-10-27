from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateSalesEntry(BaseModel):
    quotation_sent_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    po_received_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    po_expected_tomorrow_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    po_expected_this_week_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)

    model_config = ConfigDict(extra="forbid")


class SetMonthlyTarget(BaseModel):
    user_id: int = Field(gt=0)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=9999)
    target_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)

    model_config = ConfigDict(extra="forbid")


class SetAnnualSalary(BaseModel):
    user_id: int = Field(gt=0)
    year: int = Field(ge=2000, le=9999)
    annual_salary: Decimal = Field(ge=0, max_digits=14, decimal_places=2)

    model_config = ConfigDict(extra="forbid")

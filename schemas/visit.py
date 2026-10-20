from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class VisitOutcome(str, Enum):
    positive = "Positive"
    follow_up = "Follow-up"
    not_interested = "Not Interested"


class CreateVisit(BaseModel):
    visit_date: date
    visit_location: str
    contacted_person: str
    designation: str | None = None
    outcome: VisitOutcome
    remark: str

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("visit_location", "contacted_person", "remark")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value

    @field_validator("designation")
    @classmethod
    def normalize_designation(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

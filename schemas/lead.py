from enum import Enum
from typing import Optional
from pydantic import BaseModel,ConfigDict, EmailStr,Field
class Lead(BaseModel):
    name: str
    company_name: str
    city: str
    state: str 
    contact_number:str|None = None
    enquiry_type:str|None = None
    email: str |None = None
    requirement: str |None = None

    model_config = ConfigDict(extra="forbid")

class LeadStatus(str, Enum):
    open = "open"
    inprogress = "inprogress"
    closed = "closed"
class LeadStage(str, Enum):
    cold = "cold"
    warm = "warm"
    hot = "hot"
    poraise = "poraised"

class EditLead(BaseModel):
    name: str |None =None
    contact_number: Optional[str] = Field(
        default=None,
        pattern=r"^[6-9]\d{9}$",      # Indian 10-digit mobile
        description="Must be a valid 10-digit Indian phone number"
    )
    email: Optional[EmailStr] = None
    requirement: Optional[str] = None
    status: Optional[LeadStatus] = None
    stage: Optional[LeadStage] = None
    next_followup:str | None =None
    enquiry_type:Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    close : Optional[bool]  = False

    model_config = ConfigDict(extra="forbid")

class SearchLead(BaseModel):
    id:int |None = None
    city: str |None = None
    state: str |None = None
    enquiry_type:str |None = None
    status: Optional[LeadStatus] = None
    assigned_to: Optional[int] = None

    model_config = ConfigDict(extra="forbid")

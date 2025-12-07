from pydantic import BaseModel,ConfigDict
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

class EditLead(BaseModel):
    name: str |None =None
    contact_number:str | None =None
    email: str | None =None
    requirement: str | None =None
    status: str | None =None
    stage: str | None =None
    next_followup:str | None =None
    enquiry_type:str|None = None
    status: str | None =None
    assigned_to: str | None =None

    model_config = ConfigDict(extra="forbid")

class SearchLead(BaseModel):
    id:int |None = None
    city: str |None = None
    state: str |None = None
    enquiry_type:str |None = None
    status: str | None =None
    assigned_to: str | None =None

    model_config = ConfigDict(extra="forbid")

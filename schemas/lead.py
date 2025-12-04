from pydantic import BaseModel
class Lead(BaseModel):
    name: str
    company_name: str
    city: str
    state: str 
    contact_number:str|None = None
    enquery_type:str|None = None
    email: str |None = None
    requirement: str |None = None

class EditLead(BaseModel):
    name: str |None =None
    contact_number:str | None =None
    email: str | None =None
    requirement: str | None =None
    status: str | None =None
    stage: str | None =None
    next_followup:str | None =None
    status: str | None =None
    assigned_to: str | None =None
from pydantic import BaseModel
class Lead(BaseModel):
    name: str
    company_name: str
    city: str
    state: str 
    contact:int
    enquery_type:str
    email: str 
    requirement: str
    progress: str
    stage: str 
    next_followup:str
    status: str
    assigned_to: str

class EditLead(BaseModel):
    contact_number:int | None =None
    email: str | None =None
    requirement: str | None =None
    progress: str | None =None
    stage: str | None =None
    next_followup:str | None =None
    status: str | None =None
    assigned_to: str | None =None
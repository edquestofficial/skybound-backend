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
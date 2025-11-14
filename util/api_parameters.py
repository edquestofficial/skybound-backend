from pydantic import BaseModel

class UserData(BaseModel):
    id:str|None = None
    name:str|None = None
    role:str|None = None
    username:str|None = None
    password : str | None = None
    alias_name :str |None = None
    role_type : str | None = None

class Leads(BaseModel):
    lead_id : int | None = None
    lead_ids : list | None = None
    name: str | None = None
    company_name: str | None = None
    city: str | None = None 
    state: str | None = None
    contect:int | None = None
    inquery_type:str | None = None
    email: str | None = None
    requirement: str | None = None 
    progress: str | None  = None
    stage: str | None = None
    next_followup:str | None = None
    status: str | None = None
    assigned_to: str | None= None

class Project(BaseModel):
    project_id :int|None = None
    status : str |None = None
    assiged_to : str | None = None
    progress :str | None = None

class Attendence(BaseModel):
    username:str
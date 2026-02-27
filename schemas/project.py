from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class SearchProject(BaseModel):
    id:int |None = None
    city :str |None = None
    state:str |None =  None
    enquiry_type :str |None = None
    assigned_to : List[int] | None = None
    status : str | None = None
    stage : str | None = None
    last_id: int |None = None
    limit: int = 10

    model_config = ConfigDict(extra="forbid")

class UpdateModel(BaseModel):
    id: list[int] = Field(default_factory=list)
    assigned_to : List[int]  = []
    status : str | None = None
    stage : str | None = None

    model_config = ConfigDict(extra="forbid")
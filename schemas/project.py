from pydantic import BaseModel, ConfigDict

class SearchProject(BaseModel):
    id:int |None = None
    assigned_to : int | None = None
    status : str | None = None

    model_config = ConfigDict(extra="forbid")
from pydantic import BaseModel, ConfigDict, Field

class SearchProject(BaseModel):
    id:int |None = None
    assigned_to : int | None = None
    status : str | None = None

    model_config = ConfigDict(extra="forbid")

class UpdateModel(BaseModel):
    id: list[int] = Field(default_factory=list)
    assigned_to : int | None = None
    status : str | None = None

    model_config = ConfigDict(extra="forbid")
from pydantic import BaseModel

class Company(BaseModel):
    id : int | None = None
    name: str
    aliasname: str
    active:int | None = None
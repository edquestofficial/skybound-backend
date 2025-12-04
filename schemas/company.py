from pydantic import BaseModel

class Company(BaseModel):
    name: str
    comany_code: str
    active:int | None = None
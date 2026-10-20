from pydantic import BaseModel

class Response(BaseModel):
    status: bool
    code:int
    message: str
    error: str | None = None  # Optional field with a default value of None
    data: dict|list| None = None  # Optional field with a default value of None
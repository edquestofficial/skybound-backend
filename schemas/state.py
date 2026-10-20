from pydantic import BaseModel


class State(BaseModel):
    id:int
    name:str
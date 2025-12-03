from pydantic import BaseModel

class User(BaseModel):
    id : int | None = None
    name: str
    password: str
    aliasname:str
    username:str
    mobile:str
    image:str
    role:str | None = None

class Login(BaseModel):
    username: str
    password: str
from pydantic import BaseModel

class User(BaseModel):
    name: str
    password: str
    company_code:str
    username:str
    mobile:str
    image:str
    role:int | None = None


class Login(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    mobile:str | None = None
    image:str | None = None
    role:int | None = None
    active:int | None = None
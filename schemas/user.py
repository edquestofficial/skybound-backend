from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    name: str
    password: str
    company_code:str
    username:str
    mobile:str
    image:str
    role:int

    model_config = ConfigDict(extra="forbid")


class Login(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(extra="forbid")

class UserUpdate(BaseModel):
    name: str | None = None
    mobile:str | None = None
    image:str | None = None
    role:int | None = None
    active:int | None = None

    model_config = ConfigDict(extra="forbid")

class SerachUser(BaseModel):
    id:int | None = None
    role :int | None = None

    model_config = ConfigDict(extra="forbid")
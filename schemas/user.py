from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class User(BaseModel):
    name: str
    # password: str
    # company_code:str
    # username:str
    emailid:Optional[EmailStr] = None
    mobile:Optional[str] = Field(
        default=None,
        pattern=r"^[6-9]\d{9}$",      # Indian 10-digit mobile
        description="Must be a valid 10-digit Indian phone number"
    )
    image:str
    role:int

    model_config = ConfigDict(extra="forbid")


class Login(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(extra="forbid")

class UserUpdate(BaseModel):
    name: Optional[str] = None
    mobile:Optional[str] = Field(
        default=None,
        pattern=r"^[6-9]\d{9}$",      # Indian 10-digit mobile
        description="Must be a valid 10-digit Indian phone number"
    )
    emailid: Optional[EmailStr] = None
    image: Optional[str] = None
    role: Optional[int] = None
    active:Optional[int] = None

    model_config = ConfigDict(extra="forbid")

class SerachUser(BaseModel):
    id:int | None = None
    role :int | None = None
    active:int | None = None

    model_config = ConfigDict(extra="forbid")
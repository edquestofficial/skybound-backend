from pydantic import BaseModel, EmailStr

class EmailSchema(BaseModel):
    recipient_email: EmailStr | None = None
    subject: str | None = None
    body: str | None = None
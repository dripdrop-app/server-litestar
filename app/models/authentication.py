from pydantic import BaseModel, EmailStr, Field


class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class SessionUser(BaseModel):
    email: EmailStr
    admin: bool

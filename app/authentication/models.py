from pydantic import BaseModel, Field, EmailStr


class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

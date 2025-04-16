from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserOut(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

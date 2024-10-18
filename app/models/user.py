from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    user_id: int
    password_hash: str
    created_at: str
    last_login: Optional[str] = None

class User(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    created_at: datetime
    last_login: datetime | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
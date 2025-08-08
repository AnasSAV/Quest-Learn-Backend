from typing import Optional
from pydantic import BaseModel, Field


# Login/Register schemas
class UserLogin(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserRegister(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    full_name: str = Field(..., min_length=1, max_length=255, description="User full name")
    role: str = Field(..., regex="^(TEACHER|STUDENT)$", description="User role")


# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


# Response schemas
class LoginResponse(BaseModel):
    user: dict
    token: Token


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

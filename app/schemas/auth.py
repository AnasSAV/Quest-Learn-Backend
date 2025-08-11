from pydantic import BaseModel, EmailStr
from uuid import UUID

class RegisterRequest(BaseModel):
    email: EmailStr
    user_name:str
    password: str
    full_name: str
    role: str  # "TEACHER" or "STUDENT"

class LoginRequest(BaseModel):
    user_name: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
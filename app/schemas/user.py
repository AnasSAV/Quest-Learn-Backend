from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str

    class Config:
        from_attributes = True
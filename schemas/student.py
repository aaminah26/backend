from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional


# ✅ Used for creating/updating student
class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(gt=0, lt=150)
    email: EmailStr   # ✅ validates email format
    city: Optional[str] = None


# ✅ Used for returning data from API
class StudentResponse(BaseModel):
    id: int
    name: str
    age: int
    email: EmailStr
    city: Optional[str] = None

    # ✅ Pydantic v2 correct configuration
    model_config = ConfigDict(from_attributes=True)
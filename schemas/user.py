# schemas/user.py
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    name: str
    age: int
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True  # для SQLAlchemy моделей (раніше orm_mode = True)
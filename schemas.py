from pydantic import BaseModel, EmailStr
from typing import Optional

# Existing Product Schemas
class ProductBase(BaseModel):
    productname: str
    price: float
    in_stock: bool = True
    category: Optional[str] = "General"

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    productname: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None
    category: Optional[str] = None

class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True


# New User & Token Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# AI Streaming Schema Fix
class AIDescriptionRequest(BaseModel):
    productname: str
    price: float
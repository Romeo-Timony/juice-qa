from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class UserData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: int
    email: EmailStr
    username: Optional[str] = ""
    role: str
    deluxeToken: Optional[str] = ""
    lastLoginIp: Optional[str] = None
    profileImage: Optional[str] = None
    isActive: bool
    createdAt: str
    updatedAt: str
    deletedAt: Optional[str] = None

class UserRegistrationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    status: str
    data: UserData

class AuthData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    token: str
    bid: int
    umail: EmailStr

class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    authentication: AuthData

class AddressData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: int
    UserId: int
    country: str
    fullName: str
    mobileNum: int
    zipCode: str
    streetAddress: str
    city: str
    state: Optional[str] = None
    createdAt: str
    updatedAt: str

class AddressResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    status: str
    data: AddressData

class ValidationErrorDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    message: Optional[str] = None
    field: Optional[str] = None

class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    error: Optional[str] = None
    message: Optional[str] = None
    errors: Optional[List[ValidationErrorDetail]] = None

class ProductData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: int = Field(gt=0, description="Уникальный идентификатор товара")
    name: str = Field(min_length=1, description="Название товара")
    description: Optional[str] = ""
    price: float = Field(ge=0.0, description="Цена товара")
    deluxePrice: Optional[float] = None
    image: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class ProductSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    status: str
    data: List[ProductData]

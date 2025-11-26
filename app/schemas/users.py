from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class UserSchema(BaseModel):
    full_name: str
    email: EmailStr
    is_active: bool
    is_admin: bool

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid"
    )

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    department: str
    cpf: str
    matricula: str

class UserDetailsSchema(UserSchema):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    matricula: str
    password: str

class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    is_admin: Optional[bool] = False
    created_at: datetime
    updated_at:  Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid"
    )

class TokenResponse(BaseModel):
    access_token: str
    refresh_token:  Optional[str] = None
    token_type: str = "bearer"

class LoginResponse(BaseModel):
    token: TokenResponse
    user: UserOut

class TokenRefreshRequest(BaseModel):
    refresh_token: str
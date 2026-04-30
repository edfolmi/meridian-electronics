from pydantic import BaseModel, EmailStr, Field


class AuthRequest(BaseModel):
    email: EmailStr
    pin: str = Field(min_length=4, max_length=12)


class CustomerSession(BaseModel):
    customer_id: str
    name: str
    email: EmailStr
    role: str | None = None


class AuthResponse(BaseModel):
    ok: bool
    customer: CustomerSession | None = None
    message: str


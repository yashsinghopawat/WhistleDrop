from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    invite_code: str = Field(description="Secret code given to trusted moderators")

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        # bcrypt only supports 72 bytes (special characters can use more than 1 byte)
        if len(value.encode()) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return value


class LoginRequest(BaseModel):
    username: str
    password: str = Field(max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

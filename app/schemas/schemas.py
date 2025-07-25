from pydantic import BaseModel, EmailStr, Field
from datetime import date

class UserSignUp(BaseModel):
    firstName: str = Field(..., description="Your first name (3-70 characters)")
    lastName: str = Field(..., description="Your last name (3-70 characters)")
    country: str = Field(..., description="Your country name (e.g. Singapore)")
    phone: str = Field(..., description="Your phone number, valid for the specified country")
    email: EmailStr = Field(..., description="Valid email address")
    dob: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    gender: str = Field(..., description="Gender (please type 'male', 'female' or 'prefer not to say')")
    id_type: str = Field(..., description="Identification type (please type NRIC, PASSPORT, DRIVING LICENSE, AADHAAR, KTP, EMIRATES or CPR)")
    id_number: str = Field(..., description="Identification number corresponding to the id_type")
    password: str = Field(..., description="Password with at least 9 chars, uppercase, number, special char")
    confirm_password: str = Field(..., description="Confirm password (must match password)")


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


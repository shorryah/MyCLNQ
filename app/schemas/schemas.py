from pydantic import BaseModel, EmailStr, Field
from datetime import date

class UserSignUp(BaseModel):
    countryCode: str = Field(..., description = "Country calling code (e.g. +65)")
    phoneNumber: str = Field(..., description = "Phone number, valid for the specified country code")
    firstName: str = Field(..., min_length=3, max_length=70, description = "Your first name (3-70 characters)")
    lastName: str = Field(..., min_length=3, max_length=70, description = "Your last name (3-70 characters)")
    dateOfBirth: date = Field(..., description = "Date of birth (YYYY-MM-DD)")
    gender: str = Field(..., description = "Gender (male, female, or prefer not to say)")
    email: EmailStr = Field(..., description = "Valid email address")
    height: float = Field(..., description = "Height in centimeters (50-300 cm)")
    weight: float = Field(..., description = "Weight in kilograms (2-500 kg)")
    heightType: str = Field(..., description = "Height unit must be 'cm'")
    weightType: str = Field(..., description = "Weight unit must be 'kg'")
    password: str = Field(..., description = "Password with at least 9 characters, including uppercase, number, and special character")
    confirm_password: str = Field(..., description = "Confirm password (must match password)")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


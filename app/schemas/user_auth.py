from pydantic import BaseModel, EmailStr, constr
class UserSignUp(BaseModel):
    firstName : str
    lastName : str
    dob : str
    phone : str
    email : EmailStr
    password : constr(min_length=8)
    confirm_password : constr(min_length=8)
    

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
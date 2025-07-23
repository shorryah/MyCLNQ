from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user_auth import UserSignUp, UserLogin
from app.schemas.token import Token
from app.db.mongodb import UserDB
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.core.errors import UnauthorizedError
router = APIRouter()

@router.post("/signup", response_model=Token)
async def signup(user_data: UserSignUp):
    if UserDB.get_user_by_mail(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = get_password_hash(user_data.password)
    user = {
        "firstName": user_data.firstName,
        "lastName": user_data.lastName,
        "dob": user_data.dob,
        "phone": user_data.phone,
        "email": user_data.email,
        "hashed_password": hashed_password,
    }
    UserDB.create_user(user)

    token = create_access_token({"sub": user_data.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = UserDB.get_user_by_mail(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise UnauthorizedError()
    
    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}
from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from app.schemas.schemas import UserSignUp, UserLogin
from app.db.mongodb import users_collection 
from app.schemas.validation import validate_user_data 
import traceback
from app.core.security import create_access_token
import requests
from fastapi import HTTPException
import os

router = APIRouter()
baseurl = os.getenv("MY_CLNQ_SERVER_BASE_URL")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
def register(user: UserSignUp):
    validation_errors = validate_user_data(user)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation_errors
        )
    existing_user = users_collection.find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)

    user_dict = {
        "firstName": user.firstName,
        "lastName": user.lastName,
        "countryCode": user.countryCode,
        "mobileNumber": user.mobileNumber,
        "email": user.email.lower(),
        "dateOfBirth": str(user.dateOfBirth), 
        "gender": user.gender,
        "height": user.height,
        "weight": user.weight,
        "heightType": user.heightType,
        "weightType": user.weightType,
        "password": hashed_password,
    }

    try:
        result = users_collection.insert_one(user_dict)
        jwt_token = create_access_token(user.password)
        print(jwt_token)
        api_data = user_dict.copy()
        if "_id" in api_data:
            del api_data["_id"]  # Remove ObjectId before sending
            
        default_headers = {
            "Content-Type": "application/json",
        }
        
        response = requests.post(  # Using .post() directly is cleaner
            url=f"{baseurl}/api/v1/users/patients",
            json=api_data,  # Use the cleaned data
            headers=default_headers,
            timeout=10
        )
        print(response.json())
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except Exception as e:
        traceback.print_exc()  
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user due to server error.")

    return {"message": "User registered successfully", "user_id": str(result.inserted_id), "token" : jwt_token}



@router.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email.lower()})
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    token = create_access_token(user.password)
    return {"message": "Login successful", "token" : token}


@router.get("/all")
def get_all_users():
    users = list(users_collection.find())
    # Convert ObjectId to string for each document
    for user in users:
        user["_id"] = str(user["_id"])
    
    return {"users": users}
from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from app.schemas.schemas import UserSignUp, UserLogin
from app.db.mongodb import users_collection 
import traceback

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
def register(user: UserSignUp):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    
    existing_user = users_collection.find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)

    user_dict = {
        "firstName": user.firstName,
        "lastName": user.lastName,
        # "country": user.country,
        "mobileNumber": user.mobileNumber,
        "email": user.email.lower(),
        "dateOfBirth": str(user.dateOfBirth), 
        "gender": user.gender,
        "height": user.height,
        "weight": user.weight,
        # "id_type": user.id_type,
        # "id_number": user.id_number,
        "hashed_password": hashed_password,
    }

    try:
        result = users_collection.insert_one(user_dict)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except Exception as e:
        traceback.print_exc()  
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user due to server error.")

    return {"message": "User registered successfully", "user_id": str(result.inserted_id)}


@router.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email.lower()})
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return {"message": "Login successful"}


@router.get("/all")
def get_all_users():
    users = list(users_collection.find())
    # Convert ObjectId to string for each document
    for user in users:
        user["_id"] = str(user["_id"])
    
    return {"users": users}
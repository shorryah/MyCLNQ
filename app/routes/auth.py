from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from app.schemas.schemas import UserSignUp, UserLogin
from app.db.mongodb import users_collection 
from app.schemas.validation import validate_user_data 
import traceback

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
def register(user: UserSignUp):
    validation_errors = validate_user_data(user)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation_errors
        )
    
    if user.password != user.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    
    existing_user = users_collection.find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user.password)

    user_dict = {
        "firstName": user.firstName,
        "lastName": user.lastName,
        "country": user.country,
        "phone": user.phone,
        "email": user.email.lower(),
        "dob": str(user.dob), 
        "gender": user.gender,
        "id_type": user.id_type,
        "id_number": user.id_number,
        "hashed_password": hashed_password,
    }

    print(f"User data to insert: {user_dict}") 

    try:
        result = users_collection.insert_one(user_dict)
        print(f"Inserted user with ID: {result.inserted_id}")
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except Exception as e:
        print(f"[MongoDB insertion error]: {e}")
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
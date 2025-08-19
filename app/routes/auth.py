from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from app.schemas.schemas import UserSignUp, UserLogin, UserLogout
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
api_key_main_server = os.getenv("API_KEY_MYCLNQ_SERVER")


@router.post("/register")
def register(user: UserSignUp):
    
    # Validate the user details
    validation_errors = validate_user_data(user)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation_errors
        )
    
    # Check if user already exists 
    existing_user = users_collection.find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Create hasehed password
    hashed_password = pwd_context.hash(user.password)

    try:
        user_dict = {
            "firstName": user.firstName,
            "lastName": user.lastName,
            "countryCode": user.countryCode,
            "phoneNumber": user.mobileNumber,
            "email": user.email.lower(),
            "dateOfBirth": str(user.dateOfBirth), 
            "gender": user.gender,
            "height": user.height,
            "weight": user.weight,
            "heightType": user.heightType,
            "weightType": user.weightType,
            "password": hashed_password,
        }
        
        # Register user on main server  
        default_headers = {
            "Content-Type": "application/json",
            "apiKey": api_key_main_server
        }
        
        response = requests.post(
            url=f"{baseurl}/api/v1/users/patients",
            json=user_dict,
            headers=default_headers,
            timeout=10
        )
        data = response.json()
        
        print("Full response:", data)  # Debugging
        
        # Get the server session token and user_id
        if data.get("status") == "success":
            main_server_token = data["data"]["session"]
            main_server_id = data["data"]["user"]["_id"]
            
            user_dict.update({
                "mainServerJwt": main_server_token,
                "mainServerId": main_server_id
            })
            
            # Store user data in mongo db
            result = users_collection.insert_one(user_dict)
            
            # Create Jwt_Token on python server
            jwt_token = create_access_token(user.email.lower())
            
            # Return the user id and token
            return {
                "message": "User registered successfully", 
                "user_id": str(result.inserted_id), 
                "token": jwt_token
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=data.get("message", "Registration failed on main server")
            )
            
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not connect to main server: {str(e)}"
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login")
def login(user: UserLogin):
    
    # Check if the user present or not
    db_user = users_collection.find_one({"email": user.email.lower()})
    if not db_user:
        raise HTTPException(status_code=400, detail="Account doesn't exists!! Please Signup")
    
    # Check if the password is correct or not 
    if not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid Password")
    
    try:
        # Data to be sent to the backend
        # user_dict = {
        #     "countryCode": user.countryCode,
        #     "phoneNumber": user.phoneNumber,
        #     "email": user.email.lower(),
        #     "password": user.password
        # }
        
        # default_headers = {
        #     "Content-Type": "application/json",
        #     "apiKey": api_key_main_server
        # }
        # print(user_dict)
        # response = requests.post(
        #     url=f"{baseurl}/user/password/login",
        #     json=user_dict,
        #     headers=default_headers,
        #     timeout=10
        # )
        # data = response.json()
        
        # print("Full response:", data)  # Debugging
        
        # if data.get("status") == "success":
        #     main_server_token = data["data"]["session"]
        #     main_server_id = data["data"]["user"]["_id"]
            
        #     user_dict.update({
        #         "mainServerJwt": main_server_token,
        #         "mainServerId": main_server_id
        #     })
        #     users_collection.update_one(
        #         {"email": user.email.lower()},
        #         {"$set": {"mainServerJwt": main_server_token, "mainServerId": main_server_id}}
        #     )

        #     print(user_dict)
            # Create Jwt_Token on python server
            jwt_token = create_access_token(user.email.lower())
            
            # Return the user id and token
            return {
                "message": "User logged in successfully", 
                "token": jwt_token,
                "user": {
                    "email": db_user["email"],
                    "first_name": db_user.get("firstName", ""),
                    "last_name": db_user.get("lastName", ""),
                    "phoneNumber": db_user.get("phoneNumber", "")
                }
            }
        # else:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=data.get("message", "Registration failed on main server")
        #     )
            
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not connect to main server: {str(e)}"
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 

@router.post("/logout")
def logout(user: UserLogout):
    try:
        email = user.email.lower()
        db_user = users_collection.find_one({"email": email})
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database"
            )

        users_collection.update_one(
            {"email": email},
            {"$set": {"mainServerJwt": "", "mainServerId": ""}}
        )
        return {"message": "User Logout Successful"}
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

        
@router.get("/all")
def get_all_users():
    users = list(users_collection.find())
    # Convert ObjectId to string for each document
    for user in users:
        user["_id"] = str(user["_id"])
    
    return {"users": users}
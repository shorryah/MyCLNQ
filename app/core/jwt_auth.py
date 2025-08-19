from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
import os

# 1. This tells FastAPI how to extract the token from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def jwt_required(token: str = Depends(oauth2_scheme)):
    try:
        print("Token in backend",token)
        # 2. Decode the JWT using our secret key and algorithm
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        print("Hello = ",payload)
        # 3. Get the `sub` claim, which holds the user_id
        user_id = payload.get("email")
        print(payload.get("email"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: no user id")

        # 4. If all good, return the user_id to the route
        return user_id

    except jwt.ExpiredSignatureError:
        # If token is expired
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.JWTError:
        # If token is tampered with or invalid
        raise HTTPException(status_code=401, detail="Invalid token")

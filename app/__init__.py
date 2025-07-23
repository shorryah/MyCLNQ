from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.v1.user import auth as auth_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
)

app.include_router(auth_routes.router, prefix="/v1/user_auth")

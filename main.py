from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

app.include_router(auth.router, prefix="/auth")



'''
from app import app
import uvicorn

if __name__ == '__main__':
    uvicorn.run(debug=True, threaded=False, host='0.0.0.0', port= 5000)
'''
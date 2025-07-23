from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["myclnq_chatbot_db"]

class UserDB:
    collection = db["users"]
    
    @classmethod
    def get_user_by_mail(cls, email:str):
        print(f"Searching for user with email: {email}")
        print(f"Collection: {cls.collection.name}")
        print(cls.collection.find_one({"email": email}))
        return cls.collection.find_one({"email": email})
    
    @classmethod
    def create_user(cls, user_data:dict):
        cls.collection.insert_one(user_data)
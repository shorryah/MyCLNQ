from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
load_dotenv()

uri = os.getenv("MONGODB_URL")
print(uri)
client = MongoClient(uri, server_api=ServerApi('1'))

db = client["myclnq_chatbot_db"]
users_collection = db["user_data"]




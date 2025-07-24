from pymongo import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://shorryah:mongo123@cluster0.9cfchjz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))

db = client["myclnq_chatbot_db"]
users_collection = db["user_data"]




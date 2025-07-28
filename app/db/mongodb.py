from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()

# Get environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME")

# Initialize client and database
client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
db = client[DB_NAME]
users_collection = db[COLLECTION_NAME]



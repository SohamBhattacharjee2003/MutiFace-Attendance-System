import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "1234")
    MONGO_URI = os.getenv("MONGO_URI")

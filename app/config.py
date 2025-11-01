import os
from dotenv import load_dotenv

load_dotenv()  # load .env file

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'


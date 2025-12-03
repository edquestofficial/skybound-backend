# core/config.py
from pydantic_settings import BaseSettings
import json

class Settings(BaseSettings):
    secret_key : str
    algorithm : str
    access_token_expire_minutes : int
    
    class Config:
        env_file = ".env"

settings = Settings()

def get_query():
    with open("query.json", "r") as f:
        data = json.load(f)
    return data
db_query = get_query()


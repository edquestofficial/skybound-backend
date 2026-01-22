# core/config.py
from pydantic_settings import BaseSettings
import json
import os

class Settings(BaseSettings):
    secret_key : str
    algorithm : str
    access_token_expire_minutes : int
    
    class Config:
        env_file = ".env"

settings = Settings()

def get_query():
    query_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "query.json")
    with open(query_path, "r") as f:
        data = json.load(f)
    return data
db_query = get_query()


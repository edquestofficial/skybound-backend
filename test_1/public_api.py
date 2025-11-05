from fastapi import FastAPI, Request
import mysql.connector
from datetime import datetime

app = FastAPI()

@app.get("/company")
async def get_lead():
    return {"message": "Get Company API"}
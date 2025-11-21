import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
load_dotenv() 

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("HOST_DB"),          # your MySQL host
            user=os.getenv("USER_DB"),               # your MySQL username
            password=os.getenv("PASSWORD_DB"),     # your MySQL password
            database=os.getenv("NAME_DB")         # your database name
        )
        return connection
    except Error as e:
        print("Error while connecting to MySQL:", e)
        return None
    
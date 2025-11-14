# Make sure these imports are at the top of your routes/company.py file
import pandas as pd
import io
import numpy as np
import asyncio
from fastapi import APIRouter,File, UploadFile,Form,Depends,Request,Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import  base64
# from conn import mydb, cursor
# from util.face_match import face_encoding,incert
from db_config import get_connection
# from embedding_operation import facegenerating_embedding, face_embedding_search
import os
import shutil
import pandas as pd
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
import requests
from util.mailer import send_mail
from util.auth import verify_token, authenticate_user
from util.config import response
router = APIRouter()
security = HTTPBearer()
from .vector_store import process_registration_object, create_embedding_for_file
from  util.api_parameters import UserData


@router.post("/login")
async def companyadmin_login(userdata:UserData):
    """This API used for user log in.
        required parameters : 
            username:str,
            password:str,
            alias_name:str,
    """
    try:
        tokken =  authenticate_user(userdata)
        return tokken
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="There is an error in companyadmin_login.",
            error=str(e)
        )
    
@router.patch("/employees")
async def get_employees(request:Request,userdata:UserData,credentials: HTTPAuthorizationCredentials = Depends(security) ):
    """
    This api is used to get the employees list.
    optional parameter :
        salesman_list:bool
    """
    salesman_list = userdata.salesman_list
    connection = get_connection()
    cursor = connection.cursor(dictionary=True ,buffered=True)
    username = request.state.user[0]
    role = request.state.user[1]
    alias_name = request.state.user[2]
    try:
        if salesman_list and role.lower() in ["admin","hr"]:
            query = f"""SELECT * FROM  {alias_name}_employees WHERE active = 1 AND role = 'Salesman'"""
        elif not salesman_list and role.lower() in ["admin","hr"]:
            query = f"""SELECT * FROM  {alias_name}_employees WHERE active = 1 AND role != 'Admin'"""
        elif salesman_list and role.lower()not in ["admin","hr"]:
            return response(
            status="error",
            code=401,
            message="Only admin can access employee list",
            error="NOt authorized"
        )
        else:
            return response(
            status="error",
            code=401,
            message="Only admin can access employee list",
            error="NOt authorized"
        )
    except Exception as e :
        return response(
            status="error",
            code=500,
            message="There is an error in companyadmin_login.",
            error=str(e)
        )
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    details = []
    for data in result:
        data["photo"] = ""
    print(result)
    return response(
            status="success",
            code=200,
            message="Employee List feched successfully.",
            data=result
        )

@router.post("/update_employee")
async def update_employee(request:Request,userdata:UserData,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """This Api is used to Update the employee data.
        required parametrs:
            id:int , employee id whose data to be updated.
            name:str , employee name updated or old.
            username:str , employee username updayed or old.
            role :str , employee role updated or old.
        """
    name = userdata.name
    username = userdata.username
    role = userdata.role
    id = userdata.id
    updated_by = request.state.user[0]
    user_role = request.state.user[1]
    alias_name = request.state.user[2]
    connection = get_connection()
    cursor = connection.cursor(dictionary=True ,buffered=True)
    if user_role.lower() not in ["admin","hr"]:
        return response(
            status="error",
            code=401,
            message="Only admin and hr can update employee details",
            error="NOt authorized"
        )
    try:
        query = f"UPDATE {alias_name}_employees SET name = %s,username=%s , role = %s , modified_by = %s,modified_at= CURRENT_TIMESTAMP() WHERE id = %s "
        cursor.execute(query,(name,username,role,updated_by,id ))
        connection.commit()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message="Employee details updated Successfully."
        )
    except Exception as e :
        return response(
            status="error",
            code=500,
            message="There is some error while Updating the employee",
            error=str(e)
        )

@router.post("/employee")
async def add_employee(
    request:Request,
    name: str= Form(...) ,
    username: str = Form(...) ,
    password: str = Form(...) ,
    role: str = Form(...),
    photos: List[UploadFile] = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Add an employee, save photos to disk, insert record in DB,
    and generate face embeddings for each uploaded photo.
    """
    created_by = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    company_id = request.state.user[3]

    if role_user.lower() not in ["admin","hr"]:
        return response(
            status="error",
            code=401,
            message="Only admin and hr can add employee",
            error="NOt authorized"
        )


    try:
        base_path = r"D:\Skybound\skybound-backend\embeddingface\data"
        os.makedirs(base_path, exist_ok=True)

        # Ensure exactly 4 photos are provided
        if len(photos) != 4:
            return response(
            status="error",
            code=400,
            message="Exactly 4 photos are required."
        )

        saved_paths = []
        for photo in photos:
            file_path = os.path.join(base_path, photo.filename)
            with open(file_path, "wb") as f:
                f.write(await photo.read())
            saved_paths.append(file_path)

        print("Saved photo paths:", saved_paths)

        # Connect to the database
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        if role.lower() == "admin":
            return response(
            status="error",
            code=401,
            message="Cannot add Admin. Only Edquest can add Admin users.",
            error="NOt authorized"
        )

        # Store one representative photo (e.g., first one)
        with open(saved_paths[0], "rb") as f:
            photo_data = f.read()

        insert_query = f"""
            INSERT INTO {alias_name}_employees 
            (company_id, name, photo, username, password, role, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (company_id, name, photo_data, username, password, role, created_by))
        connection.commit()
        send  = send_mail(username,password, role)
        if send :
            print("mail send to HR.")
        else:
            print("Mail not send.")
        print("Employee inserted successfully in DB.")

        # Call face embedding function in a background thread (non-blocking)
        print("Starting face embedding generation...")
        result = await asyncio.to_thread(
            process_registration_object, 
            username, 
            name, 
            saved_paths
)


        cursor.close()
        connection.close()

        return response(
            status="success",
            code=200,
            message="Employee added Successfully.",
            data={
                "photos_saved": saved_paths,
                "embedding_results": result
            }
        )

    except Exception as e:
        print("Error:", str(e))
        return response(
            status="error",
            code=500,
            message="There is some error while adding the employee",
            error=str(e)
        )

@router.get("/role")
async def get_role(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security) ):
    username = request.state.user[0]
    role = request.state.user[1]
    alias_name = request.state.user[2]
    connection = get_connection()
    cursor = connection.cursor(dictionary=True ,buffered=True)
    if role.lower() not in ["admin","hr"]:
        return response(
            status="error",
            code=401,
            message="Only admin and HR can access roles.",
            error="NOt authorized"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True ,buffered=True)
    query = f"""SELECT * FROM  roles"""
    cursor.execute(query)
    result = cursor.fetchall()
    return response(
            status="success",
            code=200,
            message="Roles",
            data=result
            )

@router.delete("/employee")
async def delete_employee(request:Request,userdata:UserData,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """This API is used to Delete the employee.
    Required Parameter:
        id:int, Employee id to be deleted.
    
    """
    id = userdata.id
    username = request.state.user[0]
    role_user = request.state.user[1]   
    alias_name = request.state.user[2]
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if role_user.lower() not in ["admin","hr"]:
        return response(
            status="error",
            code=401,
            message="Only admin and hr can delete employee",
            error="NOt authorized"
        )
    
    try:
        cursor.execute(f"UPDATE {alias_name}_employees SET modified_by = %s,modified_at= CURRENT_TIMESTAMP(),active = 0 WHERE id = %s ", (username,id))
        connection.commit()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message="Employee Deleted Successfully.",
        )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="There is some error while Deleting the employee",
            error=str(e)
        )
    




# --- YOUR REQUIRED HEADERS ---
EXPECTED_HEADERS = [
    "s no.", "date", "name", "company name", "city", "state", "contact 1",
    "inquiry type", "e mail", "requirements", "status", "skybound person",
    "cold/hot/warm", "open/closed", "next follow up"
]
# -----------------------------
# @router.post("/setup-database")
# async def setup_database():
#     """
#     This is a one-time endpoint to create the inquiries table.
#     """
    
#     # ! IMPORTANT: Make sure this matches the table_name in your other function
#     table_name = "excel" 
    
#     # This is the SQL query from above
#     create_table_query = f"""
#     CREATE TABLE IF NOT EXISTS `{table_name}` (
#         `id` INT AUTO_INCREMENT PRIMARY KEY,
#         `date` DATETIME,
#         `name` VARCHAR(255),
#         `company name` VARCHAR(255),
#         `city` VARCHAR(255),
#         `state` VARCHAR(255),
#         `contact 1` VARCHAR(100),
#         `inquiry type` VARCHAR(255),
#         `e mail` VARCHAR(255),
#         `requirements` TEXT,
#         `status` VARCHAR(100),
#         `skybound person` VARCHAR(255),
#         `cold/hot/warm` VARCHAR(50),
#         `open/closed` VARCHAR(50),
#         `next follow up` DATETIME
#     );
#     """
    
#     connection = None
#     try:
#         connection = get_connection()
#         if not connection:
#             return JSONResponse(status_code=500, content={"error": "Database connection failed."})
        
#         cursor = connection.cursor()
#         cursor.execute(create_table_query)
#         connection.commit()
#         cursor.close()
        
#         return {"message": f"Table '{table_name}' created successfully (or already exists)."}

#     except Exception as e:
#         if connection:
#             connection.rollback()
#         return JSONResponse(
#             status_code=500,
#             content={"error": f"An error occurred: {str(e)}"}
#         )
#     finally:
#         if connection:
#             connection.close()



@router.post("/import-excel/")
async def import_excel_data(file: UploadFile = File(...)):
    """
    This endpoint validates an Excel file's headers (case-insensitive)
    and, if valid, inserts the data into a MySQL database.
    """
    connection = None  # Initialize connection to None
    try:
        # Read the file's content into memory
        contents = await file.read()
        buffer = io.BytesIO(contents)
        df = pd.read_excel(buffer)

        # --- 1. Header Validation ---
        
        # Create a mapping of {Original Header: lowercase_header}
        header_map = {col: str(col).strip().lower() for col in df.columns}
        
        # Get a set of the standardized headers from the file
        standardized_file_headers = set(header_map.values())
        
        # Get a set of your required headers
        required_set = set(EXPECTED_HEADERS)

        # Check if all required headers are present in the file
        if not required_set.issubset(standardized_file_headers):
            missing_headers = list(required_set - standardized_file_headers)
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid file format. Missing required headers.",
                    "missing": missing_headers
                }
            )

# --- 2. Data Processing (ALL FIXES APPLIED) ---
        
        # Rename the DataFrame columns to your standardized lowercase names
        df = df.rename(columns=header_map)
        
        # --- FIX 1: Handle NaN, empty strings, and single spaces ---
        # This replaces all of them with None, which becomes NULL in MySQL
        df = df.replace({np.nan: None, '': None, ' ': None})
        
        # --- FIX 2: Handle bad DATE columns ---
        # 'errors=coerce' turns any bad date (like 'pending') into 'NaT'
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['next follow up'] = pd.to_datetime(df['next follow up'], errors='coerce')
        
        # --- FIX 3: Handle bad NUMBER columns ---
        # This fixes errors like "Incorrect integer value: ' ' for column 's no.'"
        # It turns any bad number (like 'N/A' or text) into 'NaN' (Not a Number)
        df['s no.'] = pd.to_numeric(df['s no.'], errors='coerce')
        
        # --- FIX 4: Convert all 'NaT' and 'NaN' into None ---
        # This final step makes the data safe for MySQL, which accepts NULL.
        # This single line replaces BOTH the old .replace({np.nan: None})
        # and .replace({pd.NaT: None})
        df = df.replace({pd.NaT: None, np.nan: None})        
        # Convert the DataFrame to a list of dictionaries
        data_rows = df.to_dict(orient="records")

        # --- 3. Database Insertion ---
        
        # ! IMPORTANT: Change this to your actual table name
        table_name = "excel" 
        
        connection = get_connection()
        if not connection:
            return JSONResponse(status_code=500, content={"error": "Database connection failed."})
        
        cursor = connection.cursor()

        # Build the SQL query dynamically
        # The backticks `` are important for names with spaces or symbols
        sql_columns = ", ".join([f"`{h}`" for h in EXPECTED_HEADERS])
        
        # This creates `(%s, %s, %s, ...)`
        sql_placeholders = ", ".join(["%s"] * len(EXPECTED_HEADERS))
        
        insert_query = f"INSERT INTO {table_name} ({sql_columns}) VALUES ({sql_placeholders})"
        
        # Prepare all rows for batch insertion
        rows_to_insert = []
        for row in data_rows:
            # Create a tuple of values *in the correct order*
            values_tuple = tuple(row[h] for h in EXPECTED_HEADERS)
            rows_to_insert.append(values_tuple)

        # Execute all inserts in a single, efficient transaction
        if rows_to_insert:
            cursor.executemany(insert_query, rows_to_insert)
            connection.commit()
            
        cursor.close()

        return {
            "message": "File validated and data saved successfully!",
            "filename": file.filename,
            "records_saved": len(rows_to_insert)
        }

    except Exception as e:
        # If anything goes wrong, roll back any changes
        if connection:
            connection.rollback()
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred: {str(e)}"}
        )
    finally:
        # Ensure the file and database connection are always closed
        if connection:
            connection.close()
        await file.close()
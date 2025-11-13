# Make sure these imports are at the top of your routes/company.py file
import asyncio
from fastapi import APIRouter, File, UploadFile, Form, Depends, Request, HTTPException,Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from conn import mydb, cursor
# from util.face_match import face_encoding,incert
from db_config import get_connection
# from embedding_operation import facegenerating_embedding, face_embedding_search
import os
from typing import List
import requests
from util.mailer import send_mail
from util.auth import verify_token, authenticate_user
from util.config import response
from model.user import User
router = APIRouter()
security = HTTPBearer()

from .vector_store import process_registration_object, create_embedding_for_file

@router.post("/login")
async def companyadmin_login(user: User):
    """
    Authenticate a company administrator and generate an authentication token.

    **Description:**
    Validates user credentials (username and password) using the `authenticate_user` function.
    On success, returns an authentication token to be used for protected routes.

    **Parameters:**
    - `user` (User) — **Mandatory**. A Pydantic model containing `username` and `password`.

    **Returns:**
    - Success → JSON containing authentication token.
    - Failure → Error JSON if login fails or an exception occurs.
    """
    try:
        tokken =  authenticate_user(user)
        return tokken
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="There is an error in companyadmin_login.",
            error=str(e)
        )
    
@router.patch("/employees")
async def get_employees(request:Request,salesman_list:bool|None = Form(False),credentials: HTTPAuthorizationCredentials = Depends(security) ):
    """
    Fetch the list of employees based on role filters.

    **Description:**
    - Admins and HR can view all employees or only salesmen depending on `salesman_list`.
    - Other users are restricted from accessing this data.

    **Parameters:**
    - `request` (Request) — **Mandatory**. Used to access logged-in user details.
    - `salesman_list` (bool) — **Optional**. If `True`, returns only salesmen; defaults to `False` for all employees.
    - `credentials` (HTTPAuthorizationCredentials) — **Mandatory**. For authorization validation.

    **Returns:**
    - Success → List of employee records.
    - Failure → Unauthorized or error response.
    """

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
async def update_employee(request:Request,name:str=Form(...),username:str=Form(...),role:str=Form(...),id:int=Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Update employee details in the database.

    **Description:**
    Allows Admin or HR to update employee information such as name, username, and role.

    **Parameters:**
    - `request` (Request) — **Mandatory**. Provides context for logged-in user (updater).
    - `name` (str) — **Mandatory**. Updated name of the employee.
    - `username` (str) — **Mandatory**. Updated username of the employee.
    - `role` (str) — **Mandatory**. Updated role of the employee.
    - `id` (int) — **Mandatory**. Employee ID to be updated.
    - `credentials` (HTTPAuthorizationCredentials) — **Mandatory**. Used for authentication.

    **Returns:**
    - Success → Confirmation of successful update.
    - Failure → Error message if unauthorized or database issue occurs.
    """
    updated_by = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    connection = get_connection()
    cursor = connection.cursor(dictionary=True ,buffered=True)

    if not all([name, username, role, id]):
        return response(
            status="error",
            code=400,
            message="All mandatory fields (name, username, role, id) are required.",
            error="Bad Request"
        )


    if role_user.lower() not in ["admin","hr"]:
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
    Add a new employee, upload their photos, and generate face embeddings.

    **Description:**
    - Saves 4 uploaded employee photos locally.
    - Inserts employee details into the database.
    - Sends login credentials via email.
    - Generates face embeddings in the background.

    **Parameters:**
    - `request` (Request) — **Mandatory**. Used to identify creator and company context.
    - `name` (str) — **Mandatory**. Employee's full name.
    - `username` (str) — **Mandatory**. Unique username for login.
    - `password` (str) — **Mandatory**. Password for the new employee.
    - `role` (str) — **Mandatory**. Role assigned to the employee.
    - `photos` (List[UploadFile]) — **Mandatory**. Exactly 4 photos of the employee for embedding.
    - `credentials` (HTTPAuthorizationCredentials) — **Mandatory**. Token for authentication.

    **Returns:**
    - Success → JSON with saved photo paths and embedding results.
    - Failure → Error message for invalid permissions or upload issues.
    """
    created_by = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    company_id = request.state.user[3]

    if not all([name, username, password, role, photos]):
        return response(
            status="error",
            code=400,
            message="All mandatory fields (name, username, password, role, photos) are required.",
            error="Bad Request"
        )

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
    """
    Fetch all available roles.

    **Description:**
    Returns a list of all roles. Access restricted to Admin and HR users.

    **Parameters:**
    - `request` (Request) — **Mandatory**. Used to extract user role and company alias.
    - `credentials` (HTTPAuthorizationCredentials) — **Mandatory**. Used for token authentication.

    **Returns:**
    - Success → List of roles.
    - Failure → Error response if unauthorized.
    """
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
async def delete_employee(request:Request,employee_id:int=Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Soft delete an employee by deactivating their record.

    **Description:**
    Updates the `active` status to `0` for the specified employee.
    Only Admin or HR can perform this action.

    **Parameters:**
    - `request` (Request) — **Mandatory**. Used to get username, role, and alias.
    - `employee_id` (int) — **Mandatory**. ID of the employee to be deleted.
    - `credentials` (HTTPAuthorizationCredentials) — **Mandatory**. Authentication token.

    **Returns:**
    - Success → Confirmation message for deletion.
    - Failure → Unauthorized or error response.
    """
    username = request.state.user[0]
    role_user = request.state.user[1]   
    alias_name = request.state.user[2]

    if not all([employee_id]):
        return response(
            status="error",
            code=400,
            message="Employee ID is required.",
            error="Bad Request"
        )
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
        cursor.execute(f"UPDATE {alias_name}_employees SET modified_by = %s,modified_at= CURRENT_TIMESTAMP(),active = 0 WHERE id = %s ", (username,employee_id))
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


  

# @router.post("/fix-status-column")
# async def fix_status_column():
#     """
#     This is a one-time endpoint to alter the 'status' column
#     from VARCHAR to TEXT to allow longer data.
#     """
    
#     # ! IMPORTANT: Make sure this is your real table name
#     table_name = "excel" 
    
#     alter_query = f"""
#     ALTER TABLE `{table_name}` 
#     MODIFY COLUMN `status` TEXT;
#     """
    
#     connection = None
#     try:
#         connection = get_connection()
#         if not connection:
#             return JSONResponse(status_code=500, content={"error": "Database connection failed."})
        
#         cursor = connection.cursor()
#         cursor.execute(alter_query)
#         connection.commit()
#         cursor.close()
        
#         return {"message": f"Table '{table_name}' status column successfully changed to TEXT."}

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
 

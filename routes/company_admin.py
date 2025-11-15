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
from util.config import response, MESSAGES
router = APIRouter()
security = HTTPBearer()
from .vector_store import process_registration_object, create_embedding_for_file
from  util.api_parameters import UserData


@router.post("/login")
async def companyadmin_login(userdata:UserData):
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
        tokken =  authenticate_user(userdata)
        return tokken
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["LOGIN_ERROR"],
            error=str(e)
        )
    
@router.patch("/employees")
async def get_employees(request:Request,userdata:UserData,credentials: HTTPAuthorizationCredentials = Depends(security) ):
    """
    This api is used to get the employees list.
    optional parameter :
        salesman_list:bool
    """
    role_type = userdata.role_type
    print("Role type received:", role_type)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True ,buffered=True)
    username = request.state.user[0]
    role = request.state.user[1]
    alias_name = request.state.user[2]
    try:
        if role_type is None:
            query = f"""SELECT * FROM  {alias_name}_employees WHERE active = 1 AND role != 'Admin' """
            cursor.execute(query)
        else:
            query = f"""SELECT * FROM  {alias_name}_employees WHERE active = 1 AND role = %s """
            cursor.execute(query,(role_type,))
    except Exception as e :
        return response(
            status="error",
            code=500,
            message=MESSAGES["LOGIN_ERROR"],
            error=str(e)
        )
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
            message=MESSAGES["EMPLOYEE_LIST_SUCCESS"],
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
    if not all([name, username, role, id]):
        return response(
            status="error",
            code=400,
            message=MESSAGES["EMPLOYEE_UPDATE_MISSING_FIELDS"],
            error="Bad Request"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True ,buffered=True)
    if user_role.lower() not in ["admin","hr"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["EMPLOYEE_UPDATE_UNAUTHORIZED"],
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
            message=MESSAGES["EMPLOYEE_UPDATED_SUCCESS"]
        )
    except Exception as e :
        return response(
            status="error",
            code=500,
            message=MESSAGES["EMPLOYEE_UPDATE_FAILED"],
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
            message=MESSAGES["EMPLOYEE_ADD_MISSING_FIELDS"],
            error="Bad Request"
        )

    if role_user.lower() not in ["admin","hr"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["EMPLOYEE_ADD_UNAUTHORIZED"],
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
            message=MESSAGES["EMPLOYEE_PHOTOS_REQUIRED"]
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
            message=MESSAGES["EMPLOYEE_ADMIN_RESTRICTION"],
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
            message=MESSAGES["EMPLOYEE_ADDED_SUCCESS"],
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
            message=MESSAGES["EMPLOYEE_ADD_FAILED"],
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
    try:
        username = request.state.user[0]
        role = request.state.user[1]
        alias_name = request.state.user[2]
        connection = get_connection()
        cursor = connection.cursor(dictionary=True ,buffered=True)
        if role.lower() not in ["admin","hr"]:
            return response(
                status="error",
                code=401,
                message=MESSAGES["ROLES_UNAUTHORIZED"],
                error="NOt authorized"
            )
        connection = get_connection()
        cursor = connection.cursor(dictionary=True ,buffered=True)
        query = f"""SELECT * FROM  roles"""
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return response(
                status="success",
                code=200,
                message=MESSAGES["ROLES_SUCCESS"],
                data=result
                )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["ROLES_FETCH_ERROR"],
            error=str(e)
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

    if not all([id]):
        return response(
            status="error",
            code=400,
            message=MESSAGES["EMPLOYEE_ID_REQUIRED"],
            error="Bad Request"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if role_user.lower() not in ["admin","hr"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["EMPLOYEE_DELETE_UNAUTHORIZED"],
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
            message=MESSAGES["EMPLOYEE_DELETED_SUCCESS"],
        )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["EMPLOYEE_DELETE_FAILED"],
            error=str(e)
        )
    

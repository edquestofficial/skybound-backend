from fastapi import APIRouter, UploadFile, Form,File,Request,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import random
from db_config import get_connection
from util.config import response, MESSAGES

router = APIRouter()
security = HTTPBearer()

@router.get("/attendence")
async def get_attendence(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Retrieve all employee attendance records.

    **Description:**
    - This route can only be accessed by users with the role `admin` or `hr`.
    - Fetches all attendance records from the database.

    **Parameters:**
    - `request` (Request) — **Mandatory**. Used to extract user details (username, role, alias) from request state.
    - `credentials` (HTTPAuthorizationCredentials) — **Mandatory**. Automatically handled by `Depends(security)` for authentication.

    **Returns:**
    - JSON response containing all attendance records if authorized.
    - Error response if the user is not authorized.
    """

    username = request.state.user[0]
    role_user = request.state.user[1]   
    alias_name = request.state.user[2]


    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if role_user.lower() not in ["admin","hr"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["ATTENDANCE_UNAUTHORIZED"],
            error="NOt authorized"
        )
    # Read the uploaded image (optional — you can ignore if not needed)
    cursor.execute("SELECT * FROM attendence")
    result = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return response(
            status="success",
            code=200,
            message=MESSAGES["ATTENDANCE_FETCHED_SUCCESS"],
            data=result
            )

@router.post("/employee_attendence")
async def employee_attendence(request:Request,username:str = Form(None),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Retrieve attendance records for a specific employee.

    **Description:**
    - Returns attendance data for the given username.
    - If no username is provided, the authenticated user's attendance is returned.

    **Parameters:**
    - `request` (Request) — **Mandatory**. Contains user details like username, role, and alias.
    - `username` (str, optional) — **Optional**. If provided, fetches attendance for that username.  
      If omitted, defaults to the username from the authenticated request.
    - `credentials` (HTTPAuthorizationCredentials) — **Mandatory**. Automatically handled by `Depends(security)` for authentication.

    **Returns:**
    - JSON response with attendance records of the specified or logged-in user.
    """

    if (username == None):
        username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM attendence WHERE username = %s",(username,))
    result = cursor.fetchall()
    print(result)
    cursor.close()
    connection.close()
    return response(
            status="success",
            code=200,
            message=MESSAGES["ATTENDANCE_FETCHED_SUCCESS"],
            data=result
            )
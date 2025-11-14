from fastapi import APIRouter, UploadFile, Form,File,Request,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import random
from db_config import get_connection
from util.config import response
from util.api_parameters import Attendence
router = APIRouter()
security = HTTPBearer()

@router.get("/attendence")
async def get_attendence(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]   
    alias_name = request.state.user[2]
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if role_user.lower() not in ["admin","hr"]:
        return response(
            status="error",
            code=401,
            message="Only admin and HR can access all employee attendence.",
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
            message="Roles",
            data=result
            )

@router.post("/employee_attendence")
async def employee_attendence(request:Request,attendence:Attendence,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """This API is used to get the attendence of all employees
    optinal parameter :
    username:str,username of the employees whose addendence we want to see.
    
    """
    username = attendence.username
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
            message="Attendence fetched successfully.",
            data=result
            )
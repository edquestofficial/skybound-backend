from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException,Depends
from schemas.email import EmailSchema
from schemas.user import ChangePassword, EmailUser, User,Login, UserUpdate,SearchUser
from database import execute_company_query, execute_query,fetch_single_record
from fastapi.security import HTTPBearer
import jwt
import bcrypt

from core.config import Settings, db_query
from models.response import Response
from core.role import Role
from utility.mail import send_email_smtp
from utility.statemgmt import state
from utility.auth import role_required
from services.user import EditUser, fetchUser, reset_password,change_password
import random

settings = Settings()

router = APIRouter()
bearer = HTTPBearer()



@router.post("/register")
async def register(user: User,userinfo = Depends(role_required([Role.Admin,Role.Sales]))):
    # Check existing user
    # if "_" not in user.username:
    #     raise HTTPException(400, "Username is not correct")
    username =  state.value+"_"+user.emailid.split('@')[0]
    cur = execute_company_query(db_query['USER']['SELECT_USER_NAME'], username)
    if cur:
         return Response(
            status=False,
            code=200,
            message="User email already exist.",
            data=[]
        )
        
    password  = random.randint(10_000_000, 99_999_999)
    hashed = hash_password(password)
    # print("Passw0rd",hashed)
    execute_company_query(db_query['USER']['INSERT'], user.name, hashed, username, user.mobile, user.emailid, user.role,1,user.image,userinfo['role'])

    email_data = EmailSchema()
    email_data.recipient_email = user.emailid
    email_data.body = f"""Hi {user.name.capitalize()},

Your account has been successfully created. Below are your login credentials:

Username: {username}
Password: {password}

Please keep this information secure and do not share it with anyone.

If you have any questions or need assistance logging in, feel free to contact our support team.

Thank you,
Skybound"""
    email_data.subject ="Your Account Has Been Successfully Created"
    result = await send_email_smtp(email_data)
    return Response(
            status=True,
            code=200,
            message="User registered successfully",
            data=[]
        )
    
# -------- Login & Get Token --------
@router.post("/login")
def login(user: Login):
    if user.username and user.username.find('_'):
      prefix =user.username.split('_')[0]
      cur = execute_query(db_query['COMPANY']['SELECT_COMPANY_ALIASNAME'], prefix)
     
      if cur :
        state.setvalue(prefix)
        user_data = fetch_single_record(db_query['USER']['SELECT_USER_NAME_PASS'], user.username) 
        if user_data and user_data["active"] == 0 :
            return Response(
                status=True,
                code=200,
                message="Your account is deactivated",
                data=[]
            )
           
        if not user_data or not verify_password(user.password, user_data["password"]):
            return Response(
                status=False,
                code=200,
                message="Invalid username or password",
                data=[]
            )
        token = create_token(user_data)
        data = {"token":token,"user":{"id":user_data["id"],"email":user_data["emailid"],"name":user_data["name"],"role":user_data["role"], "userName":user_data["username"], "mobile":user_data["mobile"]}}
        return Response(
                status=True,
                code=200,
                message="Login Successfully",
                data=data
            )
      else :
            return Response(
                status=True,
                code=200,
                message="No Company available",
                data=[]
            )

def hash_password(password: str) -> str:
    # password = password[:72]                # bcrypt max length
    hashed = bcrypt.hashpw(str(password).encode('utf-8'), bcrypt.gensalt())
    return hashed.decode() 

def verify_password(plain_pass: str, hashed_pass: str) -> bool:
    # plain_pass = plain_pass[:72]
    return bcrypt.checkpw(plain_pass.encode(), hashed_pass.encode())

def create_token(userDetails:User):
    payload = {"id":userDetails["id"], "name":userDetails["name"],"role":userDetails["role"],
               "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=30)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)



@router.post("/registerAdmin")
async def registerAdmin(company_code:str,user: User):
    # Check existing user
    if(company_code):
        state.setvalue(company_code)
        username =  state.value+"_"+user.emailid.split('@')[0]
        cur = execute_company_query(db_query['USER']['SELECT_USER_NAME'], username)
        if cur:
            raise HTTPException(400, "Username already exists")
        password = random_8_digit = random.randint(10_000_000, 99_999_999)
        hashed = hash_password(password)
        execute_company_query(db_query['USER']['INSERT'],user.name, hashed, username, user.mobile,user.emailid, user.role,1,user.image,1)
        email_data = EmailSchema()
        email_data.recipient_email = user.emailid
        email_data.body = f"""Hi {user.name.capitalize()},

Your account has been successfully created. Below are your login credentials:

Username: {username}
Password: {password}

Please keep this information secure and do not share it with anyone.

If you have any questions or need assistance logging in, feel free to contact our support team.

Thank you,
Skybound"""
        email_data.subject ="Your Account Has Been Successfully Created"
        result = await send_email_smtp(email_data)
        return Response(
            status=True,
            code=200,
            message="User registered successfully",
            data=[]
        )
    else :
     return Response(
            status=False,
            code=200,
            message="fill correct user company name",
            data=[]
        )  
    
    
@router.post("/")
def fetch(user:SearchUser,userInfo= Depends(role_required([Role.Admin, Role.Sales, Role.Engineer]))):
   return fetchUser(user,userInfo)

@router.patch("/")
def edit(id:int,user: UserUpdate,userinfo = Depends(role_required([Role.Admin, Role.Sales, Role.Engineer]))):
    if Role.Admin.value == 2 or userinfo['id'] == id :
    # Check existing user
        EditUser(id,user,userinfo['id'])
        return Response(
                status=True,
                code=200,
                message="User updated successfully",
                data=[]
            )
    else :
        return Response(
                status=False,
                code=200,
                message="Insufficient permission.",
                data=[]
            )

    
@router.get("/roles")
def fetchRole(userInfo= Depends(role_required([Role.Admin,Role.Sales, Role.Engineer]))):
  return {role.name:role.value for role in Role}

@router.post("/resetpassword")
async def resetpassword(email:EmailUser,userInfo= Depends(role_required([Role.Admin, Role.Sales,Role.HR]))):
    emailId = email.emailid
    user_data = reset_password(emailId)[0]
    if user_data and user_data["active"] == 0 :
            return Response(
                status=False,
                code=200,
                message="Your account is deactivated.",
                data=[]
            )
    password  = random.randint(10_000_000, 99_999_999)
    hashed = hash_password(password)
    # print("Passw0rd",hashed)
    
    execute_company_query(db_query['USER']['UPDATE_PASSWORD'],  hashed, emailId)

    email_data = EmailSchema()
    email_data.recipient_email = emailId
    email_data.body = f"""Hi {emailId.split('@')[0].capitalize()},

Your password has been reset successfully. Below are your new password :

Password: {password}

Please keep this information secure and do not share it with anyone.

If you have any questions or need assistance logging in, feel free to contact our support team.

Thank you,
Skybound"""
    email_data.subject ="Your Password reset successfully"
    result = await send_email_smtp(email_data)
    print(result)
    return Response(
            status=True,
            code=200,
            message="User password reset successfully",
            data=[]
        )
    

@router.post("/changepassword")
async def changepassword(changepassword:ChangePassword,userInfo= Depends(role_required([Role.Admin, Role.Sales,Role.Engineer]))):
    user_data = fetch_single_record(db_query['USER']['SELECT_USER_NAME_PASSById'], userInfo['id'])
    if user_data and user_data["active"] == 0 :
            return Response(
            status=False,
            code=200,
            message="Your account is deactivated",
            data=[]
        )
        
    if not user_data or not verify_password(changepassword.oldpassword, user_data["password"]):
         return Response(
            status=False,
            code=200,
            message="Invalid Password !",
            data=[]
        )
    hashed = hash_password(changepassword.newpassword)
    # print("Passw0rd",hashed)
    
    execute_company_query(db_query['USER']['UPDATE_PASSWORD'],  hashed, user_data['emailid'])

    email_data = EmailSchema()
    email_data.recipient_email = user_data['emailid']
    email_data.body = f"""Hi {user_data['username']},

Your password has been changed successfully. Below are your new password :

Password: {changepassword.newpassword}

Please keep this information secure and do not share it with anyone.

If you have any questions or need assistance logging in, feel free to contact our support team.

Thank you,
Skybound"""
    email_data.subject ="Your Password reset successfully"
    result = await send_email_smtp(email_data)
    return Response(
            status=True,
            code=200,
            message="User password changed successfully",
            data=[]
        )
    
     







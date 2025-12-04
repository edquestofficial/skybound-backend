from fastapi import APIRouter, HTTPException,Depends
from schemas.user import User,Login
from database import execute_company_query, execute_query,fetch_single_record
from fastapi.security import HTTPBearer
import jwt
import bcrypt

from core.config import Settings, db_query
from models.response import response
from core.role import Role
from utility.statemgmt import state
from utility.auth import role_required
from services.user import fetch_user

settings = Settings()

router = APIRouter()
bearer = HTTPBearer()



@router.post("/register")
def register(user: User,userinfo = Depends(role_required([Role.Admin,Role.Sales]))):
    # Check existing user
    if "_" not in user.username:
        raise HTTPException(400, "Username is not correct")
    cur = execute_company_query(db_query['USER']['SELECT_USER_NAME'], user.username)
    if cur:
        raise HTTPException(400, "Username already exists")

    hashed = hash_password(user.password)
    # print("Passw0rd",hashed)
    execute_company_query(db_query['USER']['INSERT'], user.name, hashed, user.username, user.mobile, user.role,1,user.image,userinfo['role'])
    
    return response(
            status="success",
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
        if not user_data or not verify_password(user.password, user_data["password"]):
            raise HTTPException(401, "Invalid username or password")
        token = create_token(user_data)
        data = {"token":token,"user":{"name":user_data["name"],"role":user_data["role"]}}
        return response(
                status="success",
                code=200,
                message="Login Successfully",
                data=data
            )
      else :
           raise HTTPException(401, "No Company available")

def hash_password(password: str) -> str:
    password = password[:72]                # bcrypt max length
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode() 

def verify_password(plain_pass: str, hashed_pass: str) -> bool:
    # plain_pass = plain_pass[:72]
    return bcrypt.checkpw(plain_pass.encode(), hashed_pass.encode())

def create_token(userDetails:User):
    payload = {"id":userDetails["id"], "name":userDetails["name"],"role":userDetails["role"]}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)



@router.post("/registerAdmin")
def registerAdmin(user: User):
    # Check existing user
    if(user.company_code):
        state.setvalue(user.company_code)
        cur = execute_company_query(db_query['USER']['SELECT_USER_NAME'], user.username)
        if cur:
            raise HTTPException(400, "Username already exists")
        hashed = hash_password(user.password)
        execute_company_query(db_query['USER']['INSERT'],user.name, hashed,user.username,user.mobile,user.role,1,user.image,1)
        
        return response(
                status="success",
                code=200,
                message="User registered successfully",
                data=[]
            )
    else :
        raise HTTPException(400,"fill correct user comapny name")
    
@router.post("/")
def fetchUser(user_id:str="",role :str = "" , userInfo= Depends(role_required([Role.Admin, Role.Sales, Role.Engineer]))):
   return fetch_user(user_id,role,userInfo)

@router.get("/poraised")
def poraised():
     return response(
                status="success",
                code=200,
                message="Po raised successfully",
                data=[]
            )




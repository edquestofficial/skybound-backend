from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from util.auth import verify_token, authenticate_user

app = FastAPI(title="MySQL FastAPI Example",
    swagger_ui_parameters={"persistAuthorization": True} )


from fastapi.middleware.cors import CORSMiddleware
# from routes.super_admin import router as super_router
from routes.company_admin import router as company_admin_router
from routes.attendence import router as attendence_router 
from routes.lead import router as lead_router
from routes.projects import router as project_router 
# from routes.face_match import router as face_match_router 

open_access = [
    "/companyadmin/login",
    "/favicon.ico",
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/secure-data"
    "/lead/leads/csv"
    "/projects/fillter_projects"
]
admin_access = ["*"]
HR_access = ["companyadmin/employees","companyadmin/employee","companyadmin/update_employee","companyadmin/role", "attendence/attendence", "attendence/employee_attendence"]

@app.middleware("http")
async def get_request_headers(request, call_next):
    requested_api = request.url.path
    if requested_api not in open_access :
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        parts = auth_header.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            raise HTTPException(status_code=401, detail="Invalid Authorization header format")

        token = parts[1].strip()
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized: No token provided")
        try:
            user_info = await verify_token(token)
            request.state.user = user_info
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Unauthorized: Invalid token .{e}")
    response = await call_next(request)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define token-based security
security = HTTPBearer()

@app.get("/secure-data")
def secure_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    return {"message": f"Your token is {token}"}

app.include_router(company_admin_router, prefix="/companyadmin")
# app.include_router(super_router, prefix="/superadmin")
app.include_router(attendence_router, prefix="/attendence")
app.include_router(lead_router, prefix="/lead")
app.include_router(project_router, prefix="/projects")

@app.get("/")
def root():
    return {"message": "Welcome to FastAPI + MySQL!"}

# @app.get("/employees")
# def get_employees():
#     connection = get_connection()
#     if connection is None:
#         raise HTTPException(status_code=500, detail="Database connection failed")
    
#     cursor = connection.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM employees;")  # Replace with your table name
#     result = cursor.fetchall()
    
#     cursor.close()
#     connection.close()
#     return {"employees": result}

# @app.get("/employee/{emp_id}")
# def get_employee(emp_id: int):
#     connection = get_connection()
#     if connection is None:
#         raise HTTPException(status_code=500, detail="Database connection failed")
    
#     cursor = connection.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM employees WHERE id = %s;", (emp_id,))
#     result = cursor.fetchone()
    
#     cursor.close()
#     connection.close()

#     if not result:
#         raise HTTPException(status_code=404, detail="Employee not found")

#     return result

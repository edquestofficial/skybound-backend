from fastapi import FastAPI, HTTPException, Depends, Request
from starlette.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from util.auth import verify_token, authenticate_user # Make sure verify_token exists!

from fastapi.middleware.cors import CORSMiddleware
from routes.company_admin import router as company_admin_router
from routes.attendence import router as attendence_router 
from routes.lead import router as lead_router
from routes.projects import router as project_router 
# from routes.super_admin import router as super_router
# from routes.face_match import router as face_match_router 

app = FastAPI(title="MySQL FastAPI Example",
    swagger_ui_parameters={"persistAuthorization": True} )

# --- 1. DEFINE OPEN ROUTES ---
OPEN_ACCESS_PREFIXES = (
    "/companyadmin/login",
    "/favicon.ico",
    "/openapi.json",
    "/docs",  
    "/redoc",
    "/secure-data"
)

# --- 2. DEFINE ROLE PERMISSIONS
API_PERMISSIONS = {
    
    # ("GET", "/login"): ["SuperAdmin"],
    # ("POST", "/company"): ["SuperAdmin"],
    # ("DELETE", "/company"): ["SuperAdmin"],
    # ("POST", "/employee"): ["SuperAdmin"], 
    # ("DELETE", "/employee"): ["SuperAdmin"], 

    # --- Lead Management Routes 
    ("POST", "/lead"): ["Admin"], 
    ("PUT", "/lead/assign_lead"): ["Admin"],
    ("PUT", "/lead/assign_bulk_lead"): ["Admin"],
    ("PATCH", "/lead/get_leads"): ["Admin", "Salesman"],
    ("GET", "/lead/filter_leads"): ["Admin", "Salesman"],
    ("PUT", "/lead/update_lead"): ["Admin"],
    ("PUT", "/lead/lead_status/"): ["Admin", "Salesman"],
    ("DELETE", "/lead/lead/"): ["Admin", "Salesman"], 
    ("GET", "/lead/count_leads"): ["Admin"],     
    ("POST", "/lead/import-excel/"): ["Admin"],
    ("GET", "/lead/leads/csv"): ["Admin"], 

    # --- Project Management Routes 
    ("PUT", "/projects/assign_project"): ["Admin"],
    ("PUT", "/projects/update_project_status"): ["Admin", "Consultant"],
    ("PUT", "/projects/raise_review_request"): ["Admin", "Consultant"],
    ("DELETE", "/projects/close_project"): ["Admin","Customer"],
    ("PATCH", "/projects/fillter_projects"): ["Admin", "Consultant"],
    ("GET", "/projects/count_projects"): ["Admin"],

    # --- Attendance Routes 
    ("GET", "/attendence"): ["Admin", "HR"], 
    ("POST", "/attendence/employee_attendence"): ["Admin", "HR", "Employee","Salesman","consultant"],
    
    # --- Company Admin Routes 
    ("PATCH", "/companyadmin/employees"): ["Admin", "HR"],
    ("POST", "/companyadmin/update_employee"): ["Admin", "HR"],
    ("POST", "/companyadmin/employee"): ["Admin", "HR"],
    ("GET", "/companyadmin/role"): ["Admin", "HR"],
    ("DELETE", "/companyadmin/employee"): ["Admin", "HR"],
}

# --- 3. FIXED MIDDLEWARE (Authentication & Authorization) ---
@app.middleware("http")
async def check_auth_and_permissions(request: Request, call_next):
    path = request.url.path
    method = request.method

    # 1. Check for open access routes (no token needed)
    if path == "/":
        response = await call_next(request)
        return response
        
    if path.startswith(OPEN_ACCESS_PREFIXES):
        response = await call_next(request)
        return response

    # 2. Get and validate token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return JSONResponse(status_code=401, content={"detail": "Missing Authorization header"})
    
    parts = auth_header.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        return JSONResponse(status_code=401, content={"detail": "Invalid Authorization header format"})

    token = parts[1].strip()
    if not token:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized: No token provided"})

    try:
        user_info = await verify_token(token)
        request.state.user = user_info
    except Exception as e:
        return JSONResponse(status_code=401, content={"detail": f"Unauthorized: Invalid token. {e}"})

    # 3. Authorization (Role-Based Access Control)
    try:
        # --- FIX #1: Convert role from token to lowercase ---
        role = user_info[1].lower() 
    except (TypeError, IndexError):
        # This handles if user_info is not a list or is too short
        return JSONResponse(status_code=403, content={"detail": "Forbidden: Invalid token payload."})

    if not role:
        return JSONResponse(status_code=403, content={"detail": "Forbidden: Role not found in token."})

    # 'Super Admin' gets full access to everything
    if role == "super admin": # Also checking lowercase here
        response = await call_next(request)
        return response
    
    # --- 4. PERMISSION CHECK LOGIC (This part is correct) ---
    best_match_rule_roles = None
    best_match_len = 0
    
    for (allowed_method, path_prefix), allowed_roles in API_PERMISSIONS.items():
        if method == allowed_method and path.startswith(path_prefix):
            if len(path_prefix) > best_match_len:
                best_match_len = len(path_prefix)
                best_match_rule_roles = allowed_roles
    
    if best_match_rule_roles is None:
        return JSONResponse(status_code=403, content={"detail": f"Forbidden: No access rule defined for this resource: {method} {path}"})

    # --- FIX #2: Convert allowed roles to lowercase for comparison ---
    allowed_roles_lower = [r.lower() for r in best_match_rule_roles]

    if role in allowed_roles_lower:
        response = await call_next(request)
        return response
    else:
        # Show the original role casing in the error for better debugging
        return JSONResponse(status_code=403, content={"detail": f"Forbidden: Role '{user_info[1]}' cannot access this resource."})


# --- 4. CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. ROUTER INCLUDES ---
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




# from fastapi import FastAPI, HTTPException, Depends
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from util.auth import verify_token, authenticate_user

# app = FastAPI(title="MySQL FastAPI Example",
#     swagger_ui_parameters={"persistAuthorization": True} )


 
# from fastapi.middleware.cors import CORSMiddleware
# # from routes.super_admin import router as super_router
# from routes.company_admin import router as company_admin_router
# from routes.attendence import router as attendence_router 
# from routes.lead import router as lead_router
# from routes.projects import router as project_router 
# # from routes.face_match import router as face_match_router 

# open_access = [
#     "/companyadmin/login",
#     "/favicon.ico",
#     "/openapi.json",
#     "/docs",
#     "/docs/oauth2-redirect",
#     "/redoc",
#     "/secure-data"
# ]
# admin_access = ["*"]
# HR_access = ["companyadmin/employees","companyadmin/employee","companyadmin/update_employee","companyadmin/role", "attendence/attendence", "attendence/employee_attendence"]

# @app.middleware("http")
# async def get_request_headers(request, call_next):
#     requested_api = request.url.path
#     # Allow all Swagger & open routes
#     if not requested_api.startswith(("/docs", "/docs/","/companyadmin/login" ,"/openapi.json", "/redoc")):

        
    


#     # if requested_api not in open_access :
#         auth_header = request.headers.get("Authorization", "")
#         if not auth_header:
#             raise HTTPException(status_code=401, detail="Missing Authorization header")
#         parts = auth_header.split()
#         if parts[0].lower() != "bearer" or len(parts) != 2:
#             raise HTTPException(status_code=401, detail="Invalid Authorization header format")

#         token = parts[1].strip()
#         if not token:
#             raise HTTPException(status_code=401, detail="Unauthorized: No token provided")
#         try:
#             user_info = await verify_token(token)
#             request.state.user = user_info
#         except Exception as e:
#             raise HTTPException(status_code=401, detail=f"Unauthorized: Invalid token .{e}")
#     response = await call_next(request)
#     return response


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Define token-based security
# security = HTTPBearer()

# @app.get("/secure-data")
# def secure_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     token = credentials.credentials
#     return {"message": f"Your token is {token}"}

# app.include_router(company_admin_router, prefix="/companyadmin")
# # app.include_router(super_router, prefix="/superadmin")
# app.include_router(attendence_router, prefix="/attendence")
# app.include_router(lead_router, prefix="/lead")
# app.include_router(project_router, prefix="/projects")

# @app.get("/")
# def root():
#     return {"message": "Welcome to FastAPI + MySQL!"}
















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

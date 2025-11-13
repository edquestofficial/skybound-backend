from fastapi import APIRouter, Request,Form,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db_config import get_connection
from datetime import datetime
from util.config import response
router = APIRouter()
security = HTTPBearer()

@router.put("/assign_project")
async def assign_project(request:Request, project_id:int=Form(...), assiged_to:str= Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
    if not all([project_id, assiged_to]):
        return response(
            status="error",
            code=400,
            message="All mandatory fields (project_id, assiged_to) are required.",
            error="Bad Request"
        )
    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message="Only admin can Assign Project.",
            error="NOt authorized"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(f"UPDATE {table_name} SET assigned_to = %s WHERE id = %s", (assiged_to, project_id))
        connection.commit()
        return response(
            status="success",
            code=200,
            message="Project assigned successfully",
            )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="Failed to assign Project",
            error=str(e)
        )
    
@router.put("/update_project_status")
async def update_project_status(request:Request, project_id:int=Form(...), status:str=Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if not all([project_id, status]):
        return response(
            status="error",
            code=400,
            message="All mandatory fields (project_id, status) are required.",
            error="Bad Request"
        )
    if role_user.lower() not in ["admin","consultant"]:
        return response(
            status="error",
            code=401,
            message="Only admin and consultant can update Project status.",
            error="NOt authorized"
        )
    if role_user.lower() == "consultant":
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s",(project_id,))
        project = cursor.fetchone()
        if not project:
            return response(
                    status="error",
                    code=404,
                    message="Project not fount in the database",
                    error="Project not found"
                )
        if username != project["assigned_to"]:
            return response(
                    status="error",
                    code=401,
                    message="Only admin and assigned Consultant can update Project status.",
                    error="NOt authorized"
                    )
    try:
        cursor.execute(f"UPDATE {table_name} SET status = %s WHERE id = %s", (status, project_id))
        connection.commit()
        return response(
            status="success",
            code=200,
            message="Project Status Updated"
        )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="Failed to update project status",
            error=str(e)
            )
    
    
@router.put("/raise_review_request")
async def raise_review_request(request:Request,project_id:int=Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
    if not all([project_id]):
        return response(
            status="error",
            code=400,
            message="Project ID is required.",
            error="Bad Request"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if role_user.lower() not in ["admin","consultant"]:
        return response(
            status="error",
            code=401,
            message="Only admin and consultant can Raise Review request.",
            error="NOt authorized"
        )
    if role_user.lower() == "consultant":
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s",(project_id,))
        project = cursor.fetchone()
        if not project:
            return response(
                    status="error",
                    code=404,
                    message="Project not fount in the database",
                    error="Project not found"
                )
        if username != project["assigned_to"]:
            return response(
                    status="error",
                    code=401,
                    message="Only admin and assigned Consultant can Raise Review request..",
                    error="NOt authorized"
                    )
    try:
        cursor.execute(f"UPDATE {table_name} SET progress = %s WHERE id = %s", ("raised review", project_id))
        connection.commit()
        return response(
            status="success",
            code=200,
            message="Review request raised successfully"
        )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="Failed to update project status",
            error=str(e)
            )
    
@router.delete("/close_project")
async def close_project(request:Request,project_id:int=Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
    if not all([project_id]):
        return response(
            status="error",
            code=400,
            message="Project ID is required.",
            error="Bad Request"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message="Only admin and customer can Raise Review request.",
            error="NOt authorized"
        )
    
    try:
        cursor.execute(f"UPDATE {table_name} SET progress = %s,active = %s  WHERE id = %s", ("closed",False, project_id))
        connection.commit()
        return response(
            status="success",
            code=200,
            message="Project closed successfully"
        )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="Failed to close project",
            error=str(e)
            )
    
@router.patch("/fillter_projects")
async def filter_projects(request:Request,assigned_to: bool=Form(None),progress: str = Form(None),active: bool = Form(None),credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    parameters = []
    values = []
    if role_user.lower() not in ["admin","consultant"]:
        return response(
            status="error",
            code=401,
            message="Only admin and customer can view Projects.",
            error="NOt authorized"
        )
    if progress and progress not in ("po raised","review raised"):
        return response(
            status="error",
            code=422,
            message="Invalid progress value provided. Must be 'PO Raised' and 'review raised'",
            error="Invalid progress"
        )
    if assigned_to  :
        parameters.append(f"{table_name}.assigned_to IS %s")
        values.append(None)
    elif assigned_to == False:
        parameters.append(f"{table_name}.assigned_to IS NOT %s")
        values.append(None)
    if progress:
        parameters.append(f"{table_name}.progress = %s")
        values.append(progress)
    if active is not None:
        parameters.append(f"{table_name}.active = %s")
        values.append(active)
    filter  = " AND ".join(parameters)
    print(parameters)
    if role_user.lower() == "admin":
        if len(parameters) == 0:
            query = f"SELECT {table_name}.*,{alias_name}_leads.UNIQUE_QUERY_ID,{alias_name}_leads.name,{alias_name}_leads.company_name,{alias_name}_leads.city,{alias_name}_leads.state,{alias_name}_leads.contact_1,{alias_name}_leads.inquiry_type,{alias_name}_leads.requirement FROM {table_name} LEFT JOIN {alias_name}_leads ON {table_name}.id = {alias_name}_leads.id"
            cursor.execute(query)
        else:
            query = f"SELECT {table_name}.*,{alias_name}_leads.UNIQUE_QUERY_ID,{alias_name}_leads.name,{alias_name}_leads.company_name,{alias_name}_leads.city,{alias_name}_leads.state,{alias_name}_leads.contact_1,{alias_name}_leads.inquiry_type,{alias_name}_leads.requirement FROM {table_name} LEFT JOIN {alias_name}_leads ON {table_name}.id = {alias_name}_leads.id WHERE "+ filter
            cursor.execute(query,tuple(values))
    else:
        if len(parameters) == 0:
                query = f"SELECT {table_name}.*,{alias_name}_leads.UNIQUE_QUERY_ID,{alias_name}_leads.name,{alias_name}_leads.company_name,{alias_name}_leads.city,{alias_name}_leads.state,{alias_name}_leads.contact_1,{alias_name}_leads.inquiry_type,{alias_name}_leads.requirement FROM {table_name} LEFT JOIN {alias_name}_leads ON {table_name}.id = {alias_name}_leads.id WHERE {table_name}.assigned_to = %s"
                cursor.execute(query,(username,))
        else:
            query = f"SELECT {table_name}.*,{alias_name}_leads.UNIQUE_QUERY_ID,{alias_name}_leads.name,{alias_name}_leads.company_name,{alias_name}_leads.city,{alias_name}_leads.state,{alias_name}_leads.contact_1,{alias_name}_leads.inquiry_type,{alias_name}_leads.requirement FROM {table_name} LEFT JOIN {alias_name}_leads ON {table_name}.id = {alias_name}_leads.id WHERE {table_name}.assigned_to = %s" + filter
            cursor.execute(query,(username).append(tuple(values)))
    try:
        projects = cursor.fetchall()
        return response(
            status="success",
            code=200,
            message="project feached successfully.",
            data=projects
            )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="Failed to close project",
            error=str(e)
            )
    

@router.get("/count_projects")
async def count_leads(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security)):
    alias_name = request.state.user[2]
    role_user = request.state.user[1]
    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message="Only admin can get Project counts.",
            error="NOt authorized"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = f"""
            SELECT 
                COUNT(*) AS total_project,
                SUM(CASE WHEN progress = 'po raised' AND assigned_to IS NULL THEN 1 ELSE 0 END) AS unassigned_projects,
                SUM(CASE WHEN progress = 'closed' THEN 1 ELSE 0 END) AS closed_project,
                SUM(CASE WHEN progress = 'review request' THEN 1 ELSE 0 END) AS review_raised_project
            FROM {alias_name}_projects;
            """
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message="projects count feched successfully.",
            data=result
        )
    except Exception as e:
        print("Error while counting projects:", e)
        return response(
            status="error",
            code=500,
            message="Failed to fetch project count",
            error=str(e))
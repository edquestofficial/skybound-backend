from fastapi import APIRouter, Request,Form,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db_config import get_connection
from zoneinfo import ZoneInfo
from datetime import datetime
from util.config import response
import json

router = APIRouter()
security = HTTPBearer()

@router.put("/assign_project")
async def assign_project(request:Request, project_id:int=Form(...), assiged_to:str= Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
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
    name = request.state.user[4]
    table_name = f"{alias_name}_projects"
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    tem = {
        "status" : status,
        "Date" : datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
        "By":name
    }
    if role_user.lower() not in ["admin","consultant","implementation_engineer"]:
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
        cursor.execute(f"UPDATE {table_name}_status SET status =CONCAT(IFNULL(status,''),%s) WHERE id = %s", (json.dumps(tem), project_id))
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
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if role_user.lower() not in ["admin","consultant","implementation_engineer"]:
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
    

@router.post("/filter_projects")
async def filter_projects(
    request: Request,
    stage: str = Form(None),
    active: bool = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    inquiry_type: str = Form(None),
    assigned_to: str = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
 
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    
    table_name = f"{alias_name}_projects"
    leads_table = f"{alias_name}_leads"
    status_table = f"{alias_name}_projects_status"
    
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    parameters = []
    values = []
    
    # ROLE VALIDATION
    if role_user.lower() not in ["admin", "hr", "consultant", "implementation_engineer"]:
        return response(
            status="error",
            code=401,
            message="Only admin, HR, consultant and implementation_engineer can view projects.",
            error="Not authorized"
        )
    
    # Validate progress value - support business logic filters
    if stage == "all":
        stage = None
    
    # Normalize progress value (remove spaces for comparison)
    if stage:
        progress_normalized = stage.lower().replace(" ", "")
    
    valid_progress_values = ("in progress", "open", "review raised", "closed")
    if stage and progress_normalized not in valid_progress_values:
        return response(
            status="error",
            code=422,
            message="Invalid progress value provided. Valid values: 'in progress', 'open', 'review raised', 'closed'",
            error="Invalid progress"
        )
    
    # Build filter parameters based on business logic
    if assigned_to:
        parameters.append(f"{table_name}.assigned_to = %s")
        values.append(assigned_to)
    
    if stage:
        if progress_normalized == "in progress":
            # In progress = po raised AND assigned to someone
            parameters.append(f"{table_name}.progress = %s")
            values.append("po raised")
            parameters.append(f"{table_name}.assigned_to IS NOT NULL")
        elif progress_normalized == "open":
            # open= po raised AND assigned_to is NULL
            parameters.append(f"{table_name}.progress = %s")
            values.append("po raised")
            parameters.append(f"{table_name}.assigned_to IS NULL")
        elif progress_normalized == "review raised":
            # Review raised = raised review
            parameters.append(f"{table_name}.progress = %s")
            values.append("raised review")
        elif progress_normalized == "closed":
            # Closed = closed
            parameters.append(f"{table_name}.progress = %s")
            values.append("closed")
    
    if active is not None:
        parameters.append(f"{table_name}.active = %s")
        values.append(active)
    
    if city:
        parameters.append(f"{leads_table}.city = %s")
        values.append(city)
    
    if state:
        parameters.append(f"{leads_table}.state = %s")
        values.append(state)
    
    if inquiry_type:
        parameters.append(f"{leads_table}.inquiry_type = %s")
        values.append(inquiry_type)
    
    # Auto-filter for consultant role
    if role_user.lower() == "consultant" and not assigned_to:
        parameters.append(f"{table_name}.assigned_to = %s")
        values.append(username)
    
    filter_clause = " AND ".join(parameters) if parameters else ""
    
    try:
        # Base query with JOIN to get complete lead data
        base_query = f"""
            SELECT 
                {table_name}.*,
                {leads_table}.UNIQUE_QUERY_ID,
                {leads_table}.name,
                {leads_table}.company_name,
                {leads_table}.city,
                {leads_table}.state,
                {leads_table}.contact_1,
                {leads_table}.inquiry_type,
                {leads_table}.email,
                {leads_table}.requirement,
                {status_table}.status,
                {leads_table}.stage
            FROM {table_name}
            LEFT JOIN {leads_table}
            ON {table_name}.id = {leads_table}.id
            LEFT JOIN {status_table} 
            ON {status_table}.id = {table_name}.id
        """
        
        # Role-based filtering
        if role_user.lower() in ['admin', 'hr']:
            # Admin/HR see all projects (with optional filters)
            if filter_clause:
                query = base_query + " WHERE " + filter_clause
                cursor.execute(query, tuple(values))
            else:
                query = base_query
                cursor.execute(query)
        else:
            # Consultant/Implementation Engineer see only assigned projects
            if filter_clause:
                query = base_query + " WHERE " + filter_clause
                cursor.execute(query, tuple(values))
            else:
                # No filters but consultant must see only their projects
                query = base_query + f" WHERE {table_name}.assigned_to = %s"
                cursor.execute(query, (username,))
        
        print(query)
        projects = cursor.fetchall()
        
        if projects is None or len(projects) == 0:
            return response(
                status="error",
                code=404,
                message="No projects found"
            )
        
        cursor.close()
        connection.close()
        
        return response(
            status="success",
            code=200,
            message="Projects fetched successfully.",
            data=projects
        )
        
    except Exception as e:
        print("Error while filtering projects:", e)
        return response(
            status="error",
            code=500,
            message="Failed to filter projects",
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
    



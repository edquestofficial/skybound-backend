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
    
@router.post("/fillter_projects")
async def filter_projects(request:Request,assigned_to: bool=Form(None),progress: str = Form(None),active: bool = Form(None),credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    print("role>>>>>",role_user)
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    parameters = []
    values = []
    print(assigned_to)
    if role_user.lower() not in ["admin","consultant","implementation_engineer"]:
        return response(
            status="error",
            code=401,
            message="Only admin and customer can view Projects.",
            error="NOt authorized"
        )
    if progress and progress not in ("po raised","review raised","closed"):
        return response(
            status="error",
            code=422,
            message="Invalid progress value provided. Must be 'PO Raised' and 'review raised'",
            error="Invalid progress"
        )
    if assigned_to == True  :
        parameters.append(f"{table_name}.assigned_to IS NOT %s")
        values.append(None)
    elif assigned_to == False:
        parameters.append(f"{table_name}.assigned_to IS %s")
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
            query = f"SELECT {table_name}.*,{alias_name}_leads.UNIQUE_QUERY_ID,{alias_name}_leads.name,{alias_name}_leads.company_name,{alias_name}_leads.city,{alias_name}_leads.state,{alias_name}_leads.contact_1,{alias_name}_leads.inquiry_type,{alias_name}_leads.requirement FROM {table_name} LEFT JOIN {alias_name}_leads ON {table_name}.id = {alias_name}_leads.id WHERE {table_name}.assigned_to = %s AND " + filter
            # cursor.execute(query,(username).append(tuple(values)))
            # cursor.execute(query,(username,) + tuple(values))
            params = (username,) + tuple(values)
            cursor.execute(query, params)


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
    
@router.post("/filter_projects_by_progress")
async def filter_projects_by_progress(
    request: Request,
    progress: str = Form(None),     # from project table
    city: str = Form(None),         # from leads table
    state: str = Form(None),        # from leads table
    assigned_to: str = Form(None),  # from projects table
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]

    table_name = f"{alias_name}_projects"
    leads_table = f"{alias_name}_leads"

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    parameters = []
    values = []

    # ROLE VALIDATION
    if role_user.lower() not in ["admin", "consultant","implementation_engineer"]:
        return response(
            status="error",
            code=401,
            message="Only admin and consultant can view projects.",
            error="Not authorized"
        )

    # OPTIONAL progress validation
    valid_progress_values = ("open", "closed", "in progress", "review raised")
    if progress and progress.lower() not in valid_progress_values:
        return response(
            status="error",
            code=422,
            message="Invalid progress value.",
            error="Invalid progress"
        )

    # ADD progress filter IF provided
    if progress:
        parameters.append(f"{table_name}.progress = %s")
        values.append(progress)

    # OPTIONAL filters
    if city:
        parameters.append(f"{leads_table}.city = %s")
        values.append(city)

    if state:
        parameters.append(f"{leads_table}.state = %s")
        values.append(state)

    if assigned_to:
        parameters.append(f"{table_name}.assigned_to = %s")
        values.append(assigned_to)
    elif role_user.lower() == "consultant":
        # consultant sees only their own projects
        parameters.append(f"{table_name}.assigned_to = %s")
        values.append(username)

    filter_clause = " AND ".join(parameters)

    # ADMIN QUERY
    if role_user.lower() == "admin":
        if not parameters:
            query = f"""
                SELECT 
                    {table_name}.*,
                    {leads_table}.UNIQUE_QUERY_ID,
                    {leads_table}.name,
                    {leads_table}.company_name,
                    {leads_table}.city,
                    {leads_table}.state,
                    {leads_table}.contact_1,
                    {leads_table}.inquiry_type,
                    {leads_table}.requirement,
                    {leads_table}.status AS lead_status,
                    {leads_table}.stage
                FROM {table_name}
                LEFT JOIN {leads_table}
                ON {table_name}.id = {leads_table}.id
            """
            cursor.execute(query)
        else:
            query = f"""
                SELECT 
                    {table_name}.*,
                    {leads_table}.UNIQUE_QUERY_ID,
                    {leads_table}.name,
                    {leads_table}.company_name,
                    {leads_table}.city,
                    {leads_table}.state,
                    {leads_table}.contact_1,
                    {leads_table}.inquiry_type,
                    {leads_table}.requirement,
                    {leads_table}.status AS lead_status,
                    {leads_table}.stage
                FROM {table_name}
                LEFT JOIN {leads_table}
                ON {table_name}.id = {leads_table}.id
                WHERE {filter_clause}
            """
            cursor.execute(query, tuple(values))

    # CONSULTANT QUERY
    else:
        if not parameters:
            query = f"""
                SELECT 
                    {table_name}.*,
                    {leads_table}.UNIQUE_QUERY_ID,
                    {leads_table}.name,
                    {leads_table}.company_name,
                    {leads_table}.city,
                    {leads_table}.state,
                    {leads_table}.contact_1,
                    {leads_table}.inquiry_type,
                    {leads_table}.requirement,
                    {leads_table}.status AS lead_status,
                    {leads_table}.stage
                FROM {table_name}
                LEFT JOIN {leads_table}
                ON {table_name}.id = {leads_table}.id
                WHERE {table_name}.assigned_to = %s
            """
            cursor.execute(query, (username,))
        else:
            query = f"""
                SELECT 
                    {table_name}.*,
                    {leads_table}.UNIQUE_QUERY_ID,
                    {leads_table}.name,
                    {leads_table}.company_name,
                    {leads_table}.city,
                    {leads_table}.state,
                    {leads_table}.contact_1,
                    {leads_table}.inquiry_type,
                    {leads_table}.requirement,
                    {leads_table}.status AS lead_status,
                    {leads_table}.stage
                FROM {table_name}
                LEFT JOIN {leads_table}
                ON {table_name}.id = {leads_table}.id
                WHERE {table_name}.assigned_to = %s AND {filter_clause}
            """
            cursor.execute(query, (username, *values))

    try:
        projects = cursor.fetchall()
        return response(
            status="success",
            code=200,
            message="Projects filtered successfully.",
            data=projects
        )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="Failed to filter projects.",
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
    



from fastapi import APIRouter, Request,Form,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db_config import get_connection
from datetime import datetime
from util.config import response, MESSAGES
from util.config import response
from util.api_parameters import Project

router = APIRouter()
security = HTTPBearer()

@router.put("/assign_project")
async def assign_project(request:Request,project:Project,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Assign a project to a consultant.

    **Access:** Admin only.

    **Request Body:**
    - `project_id` (int): The unique ID of the project.
    - `assigned_to` (str): The username of the consultant to assign the project to.

    **Behavior:**
    - Updates the `assigned_to` field of the specified project record.
    - Only users with the `admin` role can perform this action.

    **Responses:**
    - `200`: Project assigned successfully.
    - `401`: Unauthorized access (user not admin).
    - `500`: Database or server error.
    """
    project_id = project.project_id
    assiged_to = project.assiged_to
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
    if not all([project_id, assiged_to]):
        return response(
            status="error",
            code=400,
            message=MESSAGES["PROJECT_ASSIGN_REQUIRED_FIELDS"],
            error="Bad Request"
        )
    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["PROJECT_ASSIGN_UNAUTHORIZED"],
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
            message=MESSAGES["PROJECT_ASSIGNED_SUCCESS"],
            )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["PROJECT_ASSIGN_FAILED"],
            error=str(e)
        )
    
@router.put("/update_project_status")
async def update_project_status(request:Request,project:Project,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Update the status of a project.

    **Access:** Admin or Consultant.

    **Request Body:**
    - `project_id` (int): The project ID.
    - `status` (str): The new status (e.g., "in progress", "completed", etc.).

    **Behavior:**
    - Admins can update any project status.
    - Consultants can only update status for projects assigned to them.

    **Responses:**
    - `200`: Project status updated successfully.
    - `401`: Unauthorized (consultant not assigned or insufficient role).
    - `404`: Project not found.
    - `500`: Database or server error.
    """
    project_id = project.project_id
    status = project.status
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
            message=MESSAGES["PROJECT_STATUS_REQUIRED_FIELDS"],
            error="Bad Request"
        )
    if role_user.lower() not in ["admin","consultant"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["PROJECT_STATUS_UPDATE_UNAUTHORIZED"],
            error="NOt authorized"
        )
    if role_user.lower() == "consultant":
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s",(project_id,))
        project = cursor.fetchone()
        if not project:
            return response(
                    status="error",
                    code=404,
                    message=MESSAGES["PROJECT_NOT_FOUND"],
                    error="Project not found"
                )
        if username != project["assigned_to"]:
            return response(
                    status="error",
                    code=401,
                    message=MESSAGES["PROJECT_STATUS_UPDATE_UNAUTHORIZED_ASSIGNED"],
                    error="NOt authorized"
                    )
    try:
        cursor.execute(f"UPDATE {table_name} SET status = %s WHERE id = %s", (status, project_id))
        connection.commit()
        return response(
            status="success",
            code=200,
            message=MESSAGES["PROJECT_STATUS_UPDATED"]
        )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["PROJECT_STATUS_UPDATE_FAILED"],
            error=str(e)
            )
    
    
@router.put("/raise_review_request")
async def raise_review_request(request:Request,project : Project,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Raise a review request for a project.

    **Access:** Admin or Consultant.

    **Request Body:**
    - `project_id` (int): The project ID.

    **Behavior:**
    - Marks the project’s `progress` as `"raised review"`.
    - Consultants can only raise review requests for their own projects.

    **Responses:**
    - `200`: Review request raised successfully.
    - `401`: Unauthorized.
    - `404`: Project not found.
    - `500`: Database or server error.
    """
    project_id = project.project_id
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
    if not all([project_id]):
        return response(
            status="error",
            code=400,
            message=MESSAGES["PROJECT_ID_REQUIRED"],
            error="Bad Request"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if role_user.lower() not in ["admin","consultant"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["PROJECT_REVIEW_UNAUTHORIZED"],
            error="NOt authorized"
        )
    if role_user.lower() == "consultant":
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s",(project_id,))
        project = cursor.fetchone()
        if not project:
            return response(
                    status="error",
                    code=404,
                    message=MESSAGES["PROJECT_NOT_FOUND"],
                    error="Project not found"
                )
        if username != project["assigned_to"]:
            return response(
                    status="error",
                    code=401,
                    message=MESSAGES["PROJECT_REVIEW_UNAUTHORIZED_ASSIGNED"],
                    error="NOt authorized"
                    )
    try:
        cursor.execute(f"UPDATE {table_name} SET progress = %s WHERE id = %s", ("raised review", project_id))
        connection.commit()
        return response(
            status="success",
            code=200,
            message=MESSAGES["PROJECT_REVIEW_RAISED_SUCCESS"]
        )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["PROJECT_STATUS_UPDATE_FAILED"],
            error=str(e)
            )
    
@router.delete("/close_project")
async def close_project(request:Request,project : Project,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Close an existing project.

    **Access:** Admin only.

    **Request Body:**
    - `project_id` (int): The project ID.

    **Behavior:**
    - Marks the project as `"closed"`.
    - Sets the `active` flag to `False`.

    **Responses:**
    - `200`: Project closed successfully.
    - `401`: Unauthorized (not admin).
    - `500`: Database or server error.
    """ 
    project_id = project.project_id
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    table_name = f"{alias_name}_projects"
    if not all([project_id]):
        return response(
            status="error",
            code=400,
            message=MESSAGES["PROJECT_ID_REQUIRED"],
            error="Bad Request"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["PROJECT_CLOSE_UNAUTHORIZED"],
            error="NOt authorized"
        )
    
    try:
        cursor.execute(f"UPDATE {table_name} SET progress = %s,active = %s  WHERE id = %s", ("closed",False, project_id))
        connection.commit()
        return response(
            status="success",
            code=200,
            message=MESSAGES["PROJECT_CLOSED_SUCCESS"]
        )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["PROJECT_CLOSE_FAILED"],
            error=str(e)
            )
    
@router.patch("/fillter_projects")
async def filter_projects(request:Request,project : Project,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Filter projects based on provided parameters.

    **Access:** Admin or Consultant.

    **Optional Query/Body Parameters:**
    - `assigned_to` (str, optional): Filter by consultant username.
    - `progress` (str, optional): Filter by progress (e.g., "po raised", "review raised").

    **Behavior:**
    - Admins can view all projects with filters applied.
    - Consultants can view only projects assigned to them.

    **Responses:**
    - `200`: Projects fetched successfully.
    - `401`: Unauthorized.
    - `422`: Invalid filter parameter.
    - `500`: Server or database error.
    """
    assigned_to = project.assiged_to
    progress = project.progress
    active  = None
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
            message=MESSAGES["PROJECT_VIEW_UNAUTHORIZED"],
            error="NOt authorized"
        )
    if progress and progress not in ("po raised","review raised"):
        return response(
            status="error",
            code=422,
            message=MESSAGES["PROJECT_INVALID_PROGRESS"],
            error="Invalid progress"
        )
    if assigned_to == True :
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
            query = f"SELECT {table_name}.*,{alias_name}_leads.UNIQUE_QUERY_ID,{alias_name}_leads.name,{alias_name}_leads.company_name,{alias_name}_leads.city,{alias_name}_leads.state,{alias_name}_leads.contact_1,{alias_name}_leads.inquiry_type,{alias_name}_leads.requirement FROM {table_name} LEFT JOIN {alias_name}_leads ON {table_name}.id = {alias_name}_leads.id WHERE {table_name}.assigned_to = %s" + filter
            cursor.execute(query,(username).append(tuple(values)))
    try:
        projects = cursor.fetchall()
        return response(
            status="success",
            code=200,
            message=MESSAGES["PROJECT_FETCHED_SUCCESS"],
            data=projects
            )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["PROJECT_FETCH_FAILED"],
            error=str(e)
            )
    

@router.get("/count_projects")
async def count_leads(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get summarized counts of projects.

    **Access:** Admin only.

    **Behavior:**
    - Counts total projects.
    - Counts unassigned projects (`progress = 'po raised'` and `assigned_to IS NULL`).
    - Counts closed projects (`progress = 'closed'`).
    - Counts review-requested projects (`progress = 'review request'`).

    **Responses:**
    - `200`: Project counts fetched successfully.
    - `401`: Unauthorized (not admin).
    - `500`: Database or server error.
    """
    alias_name = request.state.user[2]
    role_user = request.state.user[1]
    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["PROJECT_COUNT_UNAUTHORIZED"],
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
            message=MESSAGES["PROJECT_COUNT_SUCCESS"],
            data=result
        )
    except Exception as e:
        print("Error while counting projects:", e)
        return response(
            status="error",
            code=500,
            message=MESSAGES["PROJECT_COUNT_FAILED"],
            error=str(e))
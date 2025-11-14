from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db_config import get_connection
from datetime import datetime
from util.config import response, MESSAGES
import csv
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, File, UploadFile, Form, Depends, Request
import pandas as pd
import numpy as np
import io

router = APIRouter()
security = HTTPBearer()


@router.post("/lead")
async def add_lead(
    request:Request,
    name: str = Form(...),
    company_name: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    contect_1:int = Form(...),
    inquery_type:str = Form(...),
    email: str = Form(...),
    requirement: str = Form(...),
    progress: str = Form(...),
    stage: str = Form("open"),
    next_followup:str = Form(None),
    status: str = Form(None),
    assigned_to: str= Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
    """
    Add a new lead to the system.

    **Description:**
    This endpoint allows an **Admin** user to add a new lead into the system.
    It validates certain fields like `stage` and `progress` to ensure data consistency
    before inserting into the database.

    **Mandatory Parameters:**
    - `request` (Request): Provides user context.
    - `name` (str): Lead's name.
    - `company_name` (str): Company name of the lead.
    - `city` (str): City name.
    - `state` (str): State name.
    - `contect_1` (int): Contact number.
    - `inquery_type` (str): Type of inquiry.
    - `email` (str): Lead’s email address.
    - `requirement` (str): Requirements provided by the lead.
    - `progress` (str): Lead progress; must be one of `warm`, `hot`, `cold`, or `po raised`.

    **Optional Parameters:**
    - `stage` (str): Default `"open"`. Allowed values: `open`, `closed`, `in progress`.
    - `next_followup` (str): Optional next follow-up date.
    - `status` (str): Optional lead status.
    - `assigned_to` (str): Optional user the lead is assigned to.

    **Returns:**
    - `200`: Lead added successfully.
    - `401`: Unauthorized access.
    - `422`: Invalid data validation.
    - `500`: Server/database error.
    """

    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if not all([name, company_name, city, state, contect_1, inquery_type, email, requirement, progress]):
        return response(
            status="error",
            code=400,
            message=MESSAGES["LEAD_MISSING_FIELDS"],
            error="Bad Request"
        )

    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["LEAD_ADD_UNAUTHORIZED"],
            error="NOt authorized"
        )
    
    if stage and stage not in ("open","closed","in progress"):
        return response(
            status="error",
            code=422,
            message=MESSAGES["INVALID_STAGE"],
            error="Invalid stage"
        )
    if progress and progress not in ("warm","hot","cold","po raised"):
        return response(
            status="error",
            code=422,
            message=MESSAGES["INVALID_PROGRESS"],
            error="Invalid progress"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = f"""
        INSERT INTO {alias_name}_leads (date, name, company_name, city, state, contact_1, inquiry_type, email, requirement, status, assigned_to, progress, stage, next_followup) VALUES (CURDATE(),%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" 
    try:

        cursor.execute(query, (name, company_name, city, state, contect_1, inquery_type, email, requirement, status, assigned_to, progress, stage, next_followup))
        connection.commit() 
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message=MESSAGES["LEAD_ADDED_SUCCESS"],
            )
    except Exception as e:
        print("Error while inserting lead details:", e)
        return response(
            status="error",
            code=500,
            message=MESSAGES["LEAD_ADD_FAILED"],
            error=str(e)
        )
    

# # @router.post("/leads")
# async def get_leads(request:Request):
#     data = await request.json()
#     id= data.get("UNIQUE_QUERY_ID")
#     name = data.get("name")
#     company_name = data.get("company_name")
#     city = data.get("city")
#     state = data.get("state")
#     contect_1 = data.get("contect_1")
#     inquery_type = data.get("inquery_type")
#     email = data.get("email")
#     requirement = data.get("requirement")
#     status = data.get("status")
#     assigned_to = data.get("assigned_to")
#     progress = data.get("progress")
#     active = data.get("active")
#     next_followup = data.get("next_followup")
#     try:
#         connection = get_connection()
#         cursor = connection.cursor(dictionary=True)
#         query = f"""
#             INSERT INTO {alias_name}_leads (UNIQUE_QUERY_ID,date, name, company_name, city, state, contact_1, inquiry_type, email, requirement, status, assigned_to, progress, active, next_followup) VALUES (%s,CURDATE(),%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" 
#         cursor.execute(query, (id,name, company_name, city, state, contect_1, inquery_type, email, requirement, status, assigned_to, progress, active, next_followup))
#         connection.commit() 
#         cursor.close()
#         connection.close()
#         return {"message": "Lead added successfully"}
#     except Exception as e:
#         return {"error": "Invalid JSON data"}


@router.put("/assign_lead")
async def assign_leads(request:Request, lead_id:int=Form(...), assiged_to:str=Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Assign a single lead to an employee.

    **Description:**
    Allows only **Admin** users to assign an existing lead to a specific employee.
    Automatically updates the lead’s stage to `"in progress"`.

    **Mandatory Parameters:**
    - `request` (Request): Provides user context.
    - `lead_id` (int): ID of the lead to assign.
    - `assiged_to` (str): Username of the employee.
    - `credentials` (HTTPAuthorizationCredentials): Authentication token.

    **Returns:**
    - `200`: Lead assigned successfully.
    - `401`: Unauthorized (non-admin user).
    - `500`: Database or query error.
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if not all([lead_id, assiged_to]):
        return response(status="error", code=400, message=MESSAGES["ASSIGN_MISSING_FIELDS"], error="Bad Request")
    
    if role_user.lower() != "admin":
        return response(
            status="error",
            code=401,
            message=MESSAGES["ASSIGN_UNAUTHORIZED"],
            error="NOt authorized"
        )
    try:
        
        cursor.execute(f"UPDATE {alias_name}_leads SET stage = 'in progress', assigned_to = %s WHERE id = %s", (assiged_to, lead_id[0]))
        connection.commit()
        return response(
            status="success",
            code=200,
            message=MESSAGES["LEAD_ASSIGNED_SUCCESS"],
            )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["LEAD_ASSIGN_FAILED"],
            error=str(e)

        )
@router.put("/assign_bulk_lead")
async def assign_bulk_leads(request:Request, lead_id:list=Form(...), assiged_to:str=Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Assign multiple leads at once.

    **Description:**
    Allows an **Admin** to bulk assign multiple leads to an employee.
    Automatically sets the `stage` to `"in progress"` for all assigned leads.

    **Mandatory Parameters:**
    - `request` (Request): Provides user context.
    - `lead_id` (list[int]): List of lead IDs to assign.
    - `assiged_to` (str): Username of employee.
    - `credentials`: Authentication token.

    **Returns:**
    - `200`: Bulk assignment successful.
    - `401`: Unauthorized access.
    - `500`: Database error.
    """


    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]

    if not all([lead_id, assiged_to]):
        return response(status="error", code=400, message=MESSAGES["ASSIGN_MISSING_FIELDS"], error="Bad Request")

 
    
    if role_user.lower() != "admin":
        return response(
            status="error",
            code=401,
            message=MESSAGES["ASSIGN_UNAUTHORIZED"],
            error="NOt authorized"
        )
    try:
        if len(lead_id)==1:
            cursor.execute(f"UPDATE {alias_name}_leads SET stage = 'in progress', assigned_to = %s WHERE id = %s", (assiged_to, lead_id[0]))
        else:
            query = f"""UPDATE {alias_name}_leads SET stage = 'in progress', assigned_to = %s WHERE id IN ({','.join(['%s'] * len(lead_id))})"""
            cursor.execute(query, (assiged_to,*lead_id))
        connection.commit()
        return response(
            status="success",
            code=200,
            message=MESSAGES["LEAD_ASSIGNED_SUCCESS"],
            )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["LEAD_ASSIGN_FAILED"],
            error=str(e)
        )
    
    

@router.patch("/get_leads")
async def fetch_leads(request:Request,stage:str=Form(None),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fetch leads filtered by stage and user role.

    **Description:**
    - Admin users can view all leads.
    - Non-admin users can only view their assigned leads.
    - Supports filtering by `stage` (open/closed/in progress/all).

    **Mandatory Parameters:**
    - `request` (Request): Provides user context.

    **Optional Parameters:**
    - `stage` (str): Lead stage filter. Use `"all"` to get all leads.
    - `credentials`: Authentication token.

    **Returns:**
    - `200`: List of leads matching filters.
    - `401`: Unauthorized access.
    - `500`: Server error.
    """
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if stage == "all":
        stage = None
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        if role_user not in ['Admin']:
            if stage:
                query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s AND stage = %s "
                cursor.execute(query, (username,stage))
            else:
                query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s "
                cursor.execute(query, (username,))
        else:
            if stage:
                query  = f"SELECT * FROM {alias_name}_leads WHERE stage = %s"
                cursor.execute(query,(stage,))
            else:
                query = f"SELECT * FROM {alias_name}_leads"
                cursor.execute(query)

        leads = cursor.fetchall()
        if leads is None:
            return  response(
                status="error",
                code=404,
                message=MESSAGES["NO_LEADS_FOR_USER"]
            )
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message=MESSAGES["LEADS_FETCHED_SUCCESS"],
            data=leads
            )
            
    except Exception as e:
        print("Error while fetching leads:", e)
        return response(
            status="error",
            code=500,
            message=MESSAGES["LEADS_FETCH_FAILED"],
            error=str(e)
        )
    
@router.post("/filter_leads")
async def filter_leads(request:Request,stage:str=Form(None) ,state:str=Form(None),city :str = Form(None),Enquiry_type:str=Form(None),assigned_to:str=Form(None),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Filter leads based on multiple criteria.

    **Description:**
    Filters leads by parameters like stage, city, state, assigned_to, or inquiry type.
    Admin and HR can view all leads, while others can only view assigned ones.

    **Mandatory Parameters:**
    - `request` (Request): User context.

    **Optional Parameters:**
    - `stage` (str): One of `open`, `closed`, `in progress`.
    - `state` (str): Filter by state.
    - `city` (str): Filter by city.
    - `Enquiry_type` (str): Type of inquiry.
    - `assigned_to` (str): Username filter.
    - `credentials`: Authentication token.

    **Returns:**
    - `200`: Filtered list of leads.
    - `422`: Invalid filter input.
    - `500`: Database or server error.
    """
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    parameters = []
    values = []
    if stage == "all" or stage == "string":
        stage = None
    if city == "string":
        city = None
    if Enquiry_type == "string":
        Enquiry_type = None
    if assigned_to == "string":
        assigned_to = None
    if stage and stage not in ("open","closed","in progress"):
        return response(
            status="error",
            code=422,
            message=MESSAGES["INVALID_STAGE"],
            error="Invalid stage"
        )
    if stage:
        parameters.append("stage = %s")
        values.append(stage)
    if city:
        parameters.append("city = %s")
        values.append(city)
    if Enquiry_type:
        parameters.append("inquiry_type=%s")
        values.append(Enquiry_type)
    if assigned_to:
        parameters.append("assigned_to=%s")
        values.append(assigned_to)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # BUG 1 FIX: Check against lowercase roles
        if role_user.lower() not in ['admin', 'hr']:
            # This is the Non-Admin (Salesman, etc.) block
            if len(parameters) == 0 :
                query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s "
                cursor.execute(query, (username,))
            else:
                filter_string = " AND ".join(parameters)
                
                # BUG 2 FIX: Add the missing " AND "
                query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s AND " + filter_string
                
                # (You already fixed the tuple.append bug, good job)
                params = (username,) + tuple(values)
                cursor.execute(query, params)
        else:
            # This is the Admin/HR block (this part was correct)
            if len(parameters) == 0 :
                query = f"SELECT * FROM {alias_name}_leads"
                cursor.execute(query)
            else:
                filter_string = " AND ".join(parameters)
                query = f"SELECT * FROM {alias_name}_leads WHERE " + filter_string
                cursor.execute(query, tuple(values))
        
        print(query) # For debugging
        leads = cursor.fetchall()

        # Changed this to check for empty list as well
        if leads is None or len(leads) == 0:
            return response(
                status="success", # Still a success, just no data
                code=200, 
                message=MESSAGES["NO_LEADS_FOUND"],
                data=[] # Return an empty list
            )
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message=MESSAGES["LEADS_FETCHED_SUCCESS"],
            data=leads
            )
            
    except Exception as e:
        print("Error while fetching leads:", e)
        return response(
            status="error",
            code=500,
            message=MESSAGES["LEADS_FETCH_FAILED"],
            error=str(e)
        )
    
@router.put("/update_lead")
async def update_lead(
    request:Request,
    lead_id: int=Form(...),
    name: str = Form(...),
    company_name: str =Form(None),
    city: str = Form(None),
    state: str = Form(None),
    contect_1:int = Form(None),
    inquery_type:str = Form(None),
    email: str = Form(None),
    requirement: str = Form(None),
    status: str    = Form(None),
    assigned_to: str  = Form(None),
    progress: str = Form(None),
    stage: str =Form(None),
    next_followup:str = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
    """
    Update an existing lead record.

    **Description:**
    Allows **Admin** users to update any field of an existing lead.
    Accepts both partial and full updates.

    **Mandatory Parameters:**
    - `request` (Request): Provides user context.
    - `lead_id` (int): ID of the lead to update.
    - `name` (str): Lead name (required, even for partial update).

    **Optional Parameters:**
    - Any other field (city, state, progress, stage, etc.) can be provided optionally.
    - `credentials`: Authentication token.

    **Returns:**
    - `200`: Lead updated successfully.
    - `401`: Unauthorized user.
    - `422`: Invalid value for progress/stage.
    - `500`: Internal server error.
    """

    username = request.state.user[0]
    alias_name = request.state.user[2]
    role_user = request.state.user[1]

    if not all([lead_id, name]):
        return response(status="error", code=400, message=MESSAGES["UPDATE_MISSING_FIELDS"], error="Bad Request")


    if role_user.lower() not in ["admin",]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["UPDATE_UNAUTHORIZED"],
            error="NOt authorized"
        )
    
    if stage and stage not in ("open","closed","in progress"):
        return response(
            status="error",
            code=422,
            message=MESSAGES["INVALID_STAGE"],
            error="Invalid stage"
        )
    if progress and  progress not in ("warm","hot","cold","po raised"):
        return response(
            status="error",
            code=422,
            message=MESSAGES["INVALID_PROGRESS"],
            error="Invalid progress"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        update_fields = []
        params = []
        
        if name is not None:
            update_fields.append("name = %s")
            params.append(name)
        if company_name is not None:
            update_fields.append("company_name = %s")
            params.append(company_name)
        if city is not None:
            update_fields.append("city = %s")
            params.append(city)
        if state is not None:
            update_fields.append("state = %s")
            params.append(state)
        if contect_1 is not None:
            update_fields.append("contact_1 = %s")
            params.append(contect_1)
        if inquery_type is not None:
            update_fields.append("inquiry_type = %s")
            params.append(inquery_type)
        if requirement is not None:
            update_fields.append("requirement = %s")
            params.append(requirement)
        if email is not None:
            update_fields.append("email = %s")
            params.append(email)
        if status is not None:
            update_fields.append("status = %s")
            params.append(status)
        if assigned_to is not None:
            update_fields.append("assigned_to = %s")
            params.append(assigned_to)
        if progress is not None:
            update_fields.append("progress = %s")
            params.append(progress)
        if stage is not None:
            update_fields.append("stage = %s")
            params.append(stage)
        if next_followup is not None:
            update_fields.append("next_followup = %s")
            params.append(next_followup)
        
        if not update_fields:
            return response(
            status="error",
            code=404,
            message=MESSAGES["NO_FIELDS_TO_UPDATE"],
        )
        
        params.append(lead_id)
        query = f"UPDATE {alias_name}_leads SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, tuple(params))
        connection.commit()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message=MESSAGES["LEAD_UPDATED_SUCCESS"],
            )
    except Exception as e:
        print("Error while updating lead:", e)
        return response(
            status="error",
            code=500,
            message=MESSAGES["LEAD_UPDATE_FAILED"],
            error=str(e)
        )
@router.put("/lead_status/}")
async def update_lead_status(request:Request,lead_id: int=Form(...), status: str = Form(...),progress: str= Form(None),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Update the lead's status or progress.

    **Description:**
    Allows both **Admin** and **Salesman** to update the status or progress of a lead.
    When progress is `"po raised"`, automatically adds the lead to the projects table.

    **Mandatory Parameters:**
    - `lead_id` (int): Lead ID.
    - `status` (str): New status value.
    - `request`: User context.

    **Optional Parameters:**
    - `progress` (str): One of `warm`, `hot`, `cold`, or `po raised`.
    - `credentials`: Authentication token.

    **Returns:**
    - `200`: Lead status updated successfully.
    - `401`: Unauthorized user.
    - `500`: Error during database operation.
    """
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if role_user.lower() not in ["admin","salesman"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["STATUS_UPDATE_UNAUTHORIZED"],
            error="NOt authorized"
        )
    
    if progress and progress not in ("warm","hot","cold","po raised"):
        return response(
            status="error",
            code=422,
            message=MESSAGES["INVALID_PROGRESS"],
            error="Invalid progress"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    update_fields = []
    params = []
    update_fields.append("status = %s")
    params.append(status)
    if progress is not None and progress != "po raised":
        update_fields.append("progress = %s")
        params.append(progress)
    if progress is not None and progress == "po raised":
        try:
            query = f"SELECT * FROM {alias_name}_leads WHERE id = %s"
            cursor.execute(query, (lead_id,))
            lead = cursor.fetchone()
            if not lead:
                return response(
                    status="error",
                    code=404,
                    message=MESSAGES["LEAD_NOT_FOUND"],
                    error="lead not found"
                )
            query = f"INSERT INTO {alias_name}_projects (id) VALUES (%s)"

            if lead['assigned_to'] != username and role_user != 'Admin':
                return response(
            status="error",
            code=401,
            message=MESSAGES["STATUS_UPDATE_UNAUTHORIZED_ASSIGNED"],
            error="NOt authorized"
        )
            cursor.execute(query, (lead['id'],))
            connection.commit()

        except Exception as e:
            print("Error while fetching lead details:", e)
            return response(
            status="error",
            code=500,
            message=MESSAGES["LEAD_STATUS_UPDATE_FAILED"],
            error=str(e))


        update_fields.append("progress = %s")
        params.append(progress)
        update_fields.append("stage = %s")
        params.append("closed")
    params.append(lead_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = f"UPDATE {alias_name}_leads SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, tuple(params))
        connection.commit()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message=MESSAGES["LEAD_STATUS_UPDATED_SUCCESS"]
            )
    except Exception as e:
        print("Error while updating lead status:", e)
        return response(
            status="error",
            code=500,
            message=MESSAGES["LEAD_STATUS_UPDATE_FAILED"],
            error=str(e))
    
@router.delete("/lead/")
async def close_lead(request:Request,lead_id: int = Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Close a lead by marking its stage as 'closed'.

    **Description:**
    Allows **Admin** or assigned **Salesman** to mark a lead as closed.

    **Mandatory Parameters:**
    - `lead_id` (int): Lead ID.
    - `request`: User context.
    - `credentials`: Token for authentication.

    **Returns:**
    - `200`: Lead closed successfully.
    - `401`: Unauthorized.
    - `404`: Lead not found.
    - `500`: Database or connection error.
    """
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if not all([lead_id]):
        return response(status="error", code=400, message=MESSAGES["LEAD_ID_REQUIRED"], error="Bad Request")


    if role_user not in ['Admin',"Salesman"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["STATUS_UPDATE_UNAUTHORIZED"],
            error="NOt authorized"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = f"SELECT assigned_to FROM {alias_name}_leads WHERE id = %s"
    cursor.execute(query, (lead_id,))
    lead = cursor.fetchone()
    if not lead:
        return response(
            status="error",
            code=404,
            message=MESSAGES["LEAD_NOT_FOUND"],
            error="lead not found"
        )
                
    assigned_to = lead['assigned_to']
    if assigned_to != username and role_user != 'Admin':
        return response(
            status="error",
            code=401,
            message=MESSAGES["STATUS_UPDATE_UNAUTHORIZED_ASSIGNED"],
            error="NOt authorized"
        )
    try:
        query = f"UPDATE {alias_name}_leads SET stage = %s WHERE id = %s"
        cursor.execute(query, ("closed", lead_id))
        connection.commit()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message=MESSAGES["LEAD_CLOSED_SUCCESS"]
            )
    except Exception as e:
        print("Error while closing lead:", e)
        return response(
            status="error",
            code=500,
            message=MESSAGES["LEAD_CLOSE_FAILED"],
            error=str(e))
    
@router.get("/count_leads")
async def count_leads(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Retrieve count statistics for all leads.

    **Description:**
    Provides total leads count and counts by stage (open, closed, in progress).
    Accessible only to **Admin** users.

    **Mandatory Parameters:**
    - `request`: Provides context for alias name.
    - `credentials`: Authorization token.

    **Returns:**
    - `200`: Counts for each stage.
    - `401`: Unauthorized user.
    - `500`: Database or query error.
    """
    alias_name = request.state.user[2]
    role_user = request.state.user[1]
    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message=MESSAGES["COUNT_UNAUTHORIZED"],
            error="NOt authorized"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = f"""SELECT 
    COUNT(*) as total_leads,
    SUM(CASE WHEN stage = 'open' THEN 1 END) as open_leads,
    SUM(CASE WHEN stage = 'closed' THEN 1 END) as closed_leads,
    SUM(CASE WHEN stage = 'in progress' THEN 1 END) as in_progress_leads
    FROM {alias_name}_leads"""
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message=MESSAGES["LEAD_COUNT_SUCCESS"],
            data=result
        )
    except Exception as e:
        print("Error while counting leads:", e)
        return response(
            status="error",
            code=500,
            message=MESSAGES["LEAD_COUNT_FAILED"],
            error=str(e))


    # try:
    #     query = f"SELECT * FROM {alias_name}_leads"
    #     cursor.execute(query)
    #     result = cursor.fetchall()
        
    #     cursor.close()
    #     connection.close()
    #     return {"total_leads": total_leads}
    # except Exception as e:
    #     print("Error while counting leads:", e)
    #     return {"message": "Failed to count leads"}

    
EXPECTED_HEADERS = [
    "s no.", "date", "name", "company name", "city", "state", "contact 1",
    "inquiry type", "e mail", "requirements", "status", "skybound person",
    "cold/hot/warm", "open/closed", "next follow up"
]
# -----------------------------

@router.post("/import-excel/")
async def import_excel_data(file: UploadFile = File(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    This endpoint validates an Excel file's headers (case-insensitive)and, if valid, inserts the data into a MySQL database.
    """
    connection = None  # Initialize connection to None
    if not file:
        return response(
            status="error",
            code=400,
            message=MESSAGES["EXCEL_FILE_MANDATORY"],
            error="Bad Request"
        )
    try:
        # Read the file's content into memory
        contents = await file.read()
        buffer = io.BytesIO(contents)
        df = pd.read_excel(buffer)

        # --- 1. Header Validation ---
        header_map = {col: str(col).strip().lower() for col in df.columns}
        
        # Get a set of the standardized headers from the file
        standardized_file_headers = set(header_map.values())
        required_set = set(EXPECTED_HEADERS)

        # Check if all required headers are present in the file
        if not required_set.issubset(standardized_file_headers):
            missing_headers = list(required_set - standardized_file_headers)
            return response(
                status="error",
                code=400,
                message=MESSAGES["INVALID_FILE_FORMAT"],
                error=missing_headers
            )
# --- 2. Data Processing (ALL FIXES APPLIED) ---        
        # Rename the DataFrame columns to your standardized lowercase names
        df = df.rename(columns=header_map)
        
        # --- FIX 1: Handle NaN, empty strings, and single spaces ---
        # This replaces all of them with None, which becomes NULL in MySQL
        df = df.replace({np.nan: None, '': None, ' ': None})
        
        # --- FIX 2: Handle bad DATE columns ---
        # 'errors=coerce' turns any bad date (like 'pending') into 'NaT'
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['next follow up'] = pd.to_datetime(df['next follow up'], errors='coerce')
        
        # --- FIX 3: Handle bad NUMBER columns ---
        # This fixes errors like "Incorrect integer value: ' ' for column 's no.'"
        # It turns any bad number (like 'N/A' or text) into 'NaN' (Not a Number)
        df['s no.'] = pd.to_numeric(df['s no.'], errors='coerce')
        
        # --- FIX 4: Convert all 'NaT' and 'NaN' into None ---
        
        df = df.replace({pd.NaT: None, np.nan: None})        
        # Convert the DataFrame to a list of dictionaries
        data_rows = df.to_dict(orient="records")

        # --- 3. Database Insertion ---   
        # ! IMPORTANT: Change this to your actual table name
        table_name = "excel"         
        connection = get_connection()
        if not connection:
            return response(
                status="error",
                code=500,
                message=MESSAGES["DB_CONNECTION_FAILED"],
                error="Connection unavailable"
            )
        
        cursor = connection.cursor()

        # Build the SQL query dynamically
        # The backticks `` are important for names with spaces or symbols
        sql_columns = ", ".join([f"`{h}`" for h in EXPECTED_HEADERS])
        
        # This creates `(%s, %s, %s, ...)`
        sql_placeholders = ", ".join(["%s"] * len(EXPECTED_HEADERS))
        
        insert_query = f"INSERT INTO {table_name} ({sql_columns}) VALUES ({sql_placeholders})"
        
        # Prepare all rows for batch insertion
        rows_to_insert = []
        for row in data_rows:
            # Create a tuple of values *in the correct order*
            values_tuple = tuple(row[h] for h in EXPECTED_HEADERS)
            rows_to_insert.append(values_tuple)

        # Execute all inserts in a single, efficient transaction
        if rows_to_insert:
            cursor.executemany(insert_query, rows_to_insert)
            connection.commit()
            
        cursor.close()
        return response(
            status="success",
            code=200,
            message=MESSAGES["FILE_IMPORT_SUCCESS"],
            data={"filename": file.filename, "records_saved": len(rows_to_insert)}
        )

    except Exception as e:
        # If anything goes wrong, roll back any changes
        if connection:
            connection.rollback()
        return response(
            status="error",
            code=500,
            message=MESSAGES["FILE_IMPORT_FAILED"],
            error=str(e)
        )
    finally:
        # Ensure the file and database connection are always closed
        if connection:
            connection.close()

        await file.close()


@router.get("/leads/csv")
async def get_all_leads(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Return a downloadable CSV template containing the expected headers
    and one sample row with example values so users can download,
    edit and re-upload via `/import-excel/`.
    """
    try:
        # Example sample values for some columns — adjust as needed
        sample_values = {
            "s no.": 1,
            "date": "2025-11-10",
            "name": "John Doe",
            "company name": "Acme Corp",
            "city": "Mumbai",
            "state": "MH",
            "contact 1": "+919876543210",
            "inquiry type": "Product Demo",
            "e mail": "john.doe@example.com",
            "requirements": "Interested in pricing and timeline",
            "status": "open",
            "skybound person": "Alice",
            "cold/hot/warm": "warm",
            "open/closed": "open",
            "next follow up": "2025-11-20",
        }

        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(EXPECTED_HEADERS)

        # Build a sample row in the same order as EXPECTED_HEADERS
        sample_row = [sample_values.get(h, "") for h in EXPECTED_HEADERS]
        writer.writerow(sample_row)

        output.seek(0)
        headers = {"Content-Disposition": "attachment; filename=leads_template.csv"}
        return StreamingResponse(output, media_type="text/csv", headers=headers)
    except Exception as e:
        return response(
            status="error",
            code=500,
            message=MESSAGES["CSV_TEMPLATE_FAILED"],
            error=str(e)
        )
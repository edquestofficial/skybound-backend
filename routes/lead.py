from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db_config import get_connection
from datetime import datetime
from util.config import response
import csv
import json
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, File, UploadFile, Form, Depends, Request
import pandas as pd
import numpy as np
import io
from zoneinfo import ZoneInfo
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

    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message="Only admin can add lead.",
            error="NOt authorized"
        )
    
    if stage and stage not in ("open","closed","in progress"):
        return response(
            status="error",
            code=422,
            message="Invalid stage value provided. Must be 'open', 'closed', or 'in progress'.",
            error="Invalid stage"
        )
    if progress and progress not in ("warm","hot","cold","po raised"):
        return response(
            status="error",
            code=422,
            message="Invalid progress value provided. Must be 'Warm', 'Hot', 'Cold', or 'PO Raised'",
            error="Invalid progress"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = f"""
        INSERT INTO {alias_name}_leads (date, name, company_name, city, state, contact_1, inquiry_type, email, requirement, status, assigned_to, progress, stage, next_followup) VALUES (CURDATE(),%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" 
    try:

        cursor.execute(query, (name, company_name, city, state, contect_1, inquery_type, email, requirement, status, assigned_to, progress, stage, next_followup))
        connection.commit()
        lead_id = cursor.lastrowid
        query= f"""INSERT INTO {alias_name}_leads_status (id,status) VALUES (%s,%s)

"""     
        cursor.execute(query,(lead_id,status))
        connection.commit()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message="lead added successfully",
            )
    except Exception as e:
        print("Error while inserting lead details:", e)
        return response(
            status="error",
            code=500,
            message="Failed to add lead",
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
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    
    if role_user.lower() != "admin":
        return response(
            status="error",
            code=401,
            message="Only admin can assign lead.",
            error="NOt authorized"
        )
    try:
        
        cursor.execute(f"UPDATE {alias_name}_leads SET stage = 'in progress', assigned_to = %s WHERE id = %s", (assiged_to, lead_id))
        connection.commit()
        return response(
            status="success",
            code=200,
            message="lead assigned successfully",
            )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="Failed to assign lead",
            error=str(e)

        )
@router.put("/assign_bulk_lead")
async def assign_bulk_leads(request:Request, lead_id:list=Form(...), assiged_to:str=Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    
    if role_user.lower() != "admin":
        return response(
            status="error",
            code=401,
            message="Only admin can assign lead.",
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
            message="lead assigned successfully",
            )
    except Exception as e:
        return response(
            status="error",
            code=500,
            message="Failed to assign lead",
            error=str(e)
        )
    
    

# @router.post("/get_leads")
# async def fetch_leads(request:Request,stage:str=Form(None),credentials: HTTPAuthorizationCredentials = Depends(security)):
#     username = request.state.user[0]
#     role_user = request.state.user[1]
#     alias_name = request.state.user[2]
#     if stage == "all":
#         stage = None
#     connection = get_connection()
#     cursor = connection.cursor(dictionary=True)
#     try:
#         if role_user not in ['Admin']:
#             if stage:
#                 query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s AND stage = %s "
#                 cursor.execute(query, (username,stage))
#             else:
#                 query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s "
#                 cursor.execute(query, (username,))
#         else:
#             if stage:
#                 query  = f"SELECT * FROM {alias_name}_leads WHERE stage = %s"
#                 cursor.execute(query,(stage,))
#             else:
#                 query = f"SELECT * FROM {alias_name}_leads"
#                 cursor.execute(query)

#         leads = cursor.fetchall()
#         if leads is None:
#             return  response(
#                 status="error",
#                 code=404,
#                 message="No leads found for the use"
#             )
        
#         # Transform status column into array with single object
#         for lead in leads:
#             original_status = lead.get('status', '')
            
#             # Create a single status object
#             lead['status'] = [
#                 {
#                     "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                     "comment": original_status if original_status else "No status",
#                     "username": lead.get('assigned_to', 'Unknown'),
#                     "user_id": 1
#                 }
#             ]
        
#         cursor.close()
#         connection.close()
#         return response(
#             status="success",
#             code=200,
#             message="Leads feached successfully.",
#             data=leads
#             )
            
#     except Exception as e:
#         print("Error while fetching leads:", e)
#         return response(
#             status="error",
#             code=500,
#             message="Failed to fetch leads",
#             error=str(e)
#         )
    
@router.post("/filter_leads")
async def filter_leads(request:Request,stage:str=Form(None) ,state:str=Form(None),city :str = Form(None),Enquiry_type:str=Form(None),assigned_to:str=Form(None),credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    parameters = []
    values = []
    if stage == "all":
        stage = None
    if stage and stage not in ("open","closed","in progress"):
        return response(
            status="error",
            code=422,
            message="Invalid stage value provided. Must be 'open', 'closed', or 'in progress'.",
            error="Invalid stage"
        )
    if stage:
        parameters.append(f"{alias_name}_leads.stage = %s")
        values.append(stage)
    if state:
        parameters.append(f"{alias_name}_leads.state = %s")
        values.append(state)

    if city:
        parameters.append(f"{alias_name}_leads.city = %s")
        values.append(city)
    if Enquiry_type:
        parameters.append(f"{alias_name}_leads.inquiry_type=%s")
        values.append(Enquiry_type)
    if assigned_to:
        parameters.append(f"{alias_name}_leads.assigned_to=%s")
        values.append(assigned_to)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        if role_user not in ['Admin',"HR"]:
            if len(parameters) == 0 :
                query = f"SELECT {alias_name}_leads.*,{alias_name}_leads_status.status FROM {alias_name}_leads LEFT JOIN {alias_name}_leads_status ON {alias_name}_leads.id = {alias_name}_leads_status.id  WHERE {alias_name}_leads.assigned_to = %s "
                cursor.execute(query, (username,))
            else:
                filter  = " AND ".join(parameters)
                query = f"SELECT {alias_name}_leads.*,{alias_name}_leads_status.status FROM {alias_name}_leads LEFT JOIN {alias_name}_leads_status ON {alias_name}_leads.id = {alias_name}_leads_status.id WHERE {alias_name}_leads.assigned_to = %s"+filter
                values.insert(0,username)
                cursor.execute(query,tuple(values))
        else:
            if len(parameters) ==0 :
                filter = ""
                query = f"SELECT {alias_name}_leads.*,{alias_name}_leads_status.status FROM {alias_name}_leads LEFT JOIN {alias_name}_leads_status ON {alias_name}_leads.id = {alias_name}_leads_status.id"
                cursor.execute(query)
            else:
                filter  = " AND ".join(parameters)
                query = f"SELECT {alias_name}_leads.*,{alias_name}_leads_status.status FROM {alias_name}_leads LEFT JOIN {alias_name}_leads_status ON {alias_name}_leads.id = {alias_name}_leads_status.id WHERE "+filter
                cursor.execute(query,tuple(values))
        print(query)
        leads = cursor.fetchall()
        if leads is None:
            return response(
                status="error",
                code=404,
                message="No leads found for the use"
            )
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message="Leads feached successfully.",
            data=leads
            )
            
    except Exception as e:
        print("Error while fetching leads:", e)
        return response(
            status="error",
            code=500,
            message="Failed to fetch leads",
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

    username = request.state.user[0]
    alias_name = request.state.user[2]
    role_user = request.state.user[1]
    if role_user.lower() not in ["admin",]:
        return response(
            status="error",
            code=401,
            message="Only admin can update lead.",
            error="NOt authorized"
        )
    
    if stage and stage not in ("open","closed","in progress"):
        return response(
            status="error",
            code=422,
            message="Invalid stage value provided. Must be 'open', 'closed', or 'in progress'.",
            error="Invalid stage"
        )
    if progress and  progress not in ("warm","hot","cold","po raised"):
        return response(
            status="error",
            code=422,
            message="Invalid progress value provided. Must be 'Warm', 'Hot', 'Cold', or 'PO Raised'",
            error="Invalid progress"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        update_fields = []
        params = []
        
        if name is not None:
            update_fields.append(f"{alias_name}_leads.name = %s")
            params.append(name)
        if company_name is not None:
            update_fields.append(f"{alias_name}_leads.company_name = %s")
            params.append(company_name)
        if city is not None:
            update_fields.append(f"{alias_name}_leads.city = %s")
            params.append(city)
        if state is not None:
            update_fields.append(f"{alias_name}_leads.state = %s")
            params.append(state)
        if contect_1 is not None:
            update_fields.append(f"{alias_name}_leads.contact_1 = %s")
            params.append(contect_1)
        if inquery_type is not None:
            update_fields.append(f"{alias_name}_leads.inquiry_type = %s")
            params.append(inquery_type)
        if requirement is not None:
            update_fields.append(f"{alias_name}_leads.requirement = %s")
            params.append(requirement)
        if email is not None:
            update_fields.append(f"{alias_name}_leads.email = %s")
            params.append(email)
        if status is not None:
            update_fields.append(f"{alias_name}_leads_status.status = %s")
            params.append(status)
        if assigned_to is not None:
            update_fields.append(f"{alias_name}_leads.assigned_to = %s")
            params.append(assigned_to)
        if progress is not None:
            update_fields.append(f"{alias_name}_leads.progress = %s")
            params.append(progress)
        if stage is not None:
            update_fields.append(f"{alias_name}_leads.stage = %s")
            params.append(stage)
        if next_followup is not None:
            update_fields.append(f"{alias_name}_leads.next_followup = %s")
            params.append(next_followup)
        
        if not update_fields:
            return response(
            status="error",
            code=404,
            message="No fields to update",
        )
        
        params.append(lead_id)
        query = f"UPDATE {alias_name}_leads JOIN {alias_name}_leads_status ON {alias_name}_leads.id = {alias_name}_leads_status.id SET {', '.join(update_fields)} WHERE  {alias_name}_leads.id = %s"
        cursor.execute(query, tuple(params))
        connection.commit()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message="Lead updated successfully",
            )
    except Exception as e:
        print("Error while updating lead:", e)
        return response(
            status="error",
            code=500,
            message="Failed to fetch lead",
            error=str(e)
        )
@router.put("/lead_status")
async def update_lead_status(request:Request,lead_id: int=Form(...), status: str = Form(...),progress: str= Form(None),credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    name = request.state.user[4]
    if role_user.lower() not in ["admin","salesman","consultant","implementation_engineer"]:
        return response(
            status="error",
            code=401,
            message="Only admin, salesman, consultant and implementation_engineer can update lead status.",
            error="NOt authorized"
        )
    
    if progress and progress not in ("warm","hot","cold","po raised"):
        return response(
            status="error",
            code=422,
            message="Invalid progress value provided. Must be 'Warm', 'Hot', 'Cold', or 'PO Raised'",
            error="Invalid progress"
        )
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = f"""SELECT status from {alias_name}_leads_status WHERE id = %s"""
    cursor.execute(query,(lead_id,))
    old_status = cursor.fetchone()
    update_fields = []
    params = []
    update_fields.append(f"{alias_name}_leads_status.status = CONCAT(IFNULL({alias_name}_leads_status.status,''), %s)")
    tem = {
        "status" : status,
        "Date" : datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
        "By":name
    }
    
    status = json.dumps(tem)
    params.append(status)
    if progress is not None and progress != "po raised":
        update_fields.append(f"{alias_name}_leads.progress = %s")
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
                    message="Lead not fount in the database",
                    error="lead not found"
                )
            query = f"INSERT INTO {alias_name}_projects (id) VALUES (%s)"

            if lead['assigned_to'] != username and role_user.lower() != 'admin':
                return response(
            status="error",
            code=401,
            message="Only admin and assigned user can update lead status.",
            error="NOt authorized"
        )
            cursor.execute(query, (lead['id'],))
            connection.commit()
            query = f"INSERT INTO {alias_name}_projects_status (id) VALUES (%s)"
            cursor.execute(query, (lead['id'],))
            connection.commit()

        except Exception as e:
            print("Error while fetching lead details:", e)
            return response(
            status="error",
            code=500,
            message="Failed to fetch lead detailsd",
            error=str(e))


        update_fields.append(f"{alias_name}_leads.progress = %s")
        params.append(progress)
        update_fields.append(f"{alias_name}_leads.stage = %s")
        params.append("closed")
    params.append(lead_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = f"UPDATE {alias_name}_leads JOIN {alias_name}_leads_status ON {alias_name}_leads.id = {alias_name}_leads_status.id SET {', '.join(update_fields)} WHERE {alias_name}_leads.id = %s"
        cursor.execute(query, tuple(params))
        connection.commit()
        cursor.close()
        connection.close()
        return response(
            status="success",
            code=200,
            message="Leads status updated  successfully."
            )
    except Exception as e:
        print("Error while updating lead status:", e)
        return response(
            status="error",
            code=500,
            message="Failed to fetch lead detailsd",
            error=str(e))
    
@router.delete("/lead/")
async def close_lead(request:Request,lead_id: int = Form(...),credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if role_user not in ['Admin',"Salesman"]:
        return response(
            status="error",
            code=401,
            message="Only admin and salesman can update lead status.",
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
            message="Lead not fount in the database",
            error="lead not found"
        )
                
    assigned_to = lead['assigned_to']
    if assigned_to != username and role_user != 'Admin':
        return response(
            status="error",
            code=401,
            message="Only admin and assigned salesman can update lead status.",
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
            message="Leads closed successfully."
            )
    except Exception as e:
        print("Error while closing lead:", e)
        return response(
            status="error",
            code=500,
            message="Failed to fetch lead detailsd",
            error=str(e))
    
@router.get("/count_leads")
async def count_leads(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security)):
    alias_name = request.state.user[2]
    role_user = request.state.user[1]
    if role_user.lower() not in ["admin"]:
        return response(
            status="error",
            code=401,
            message="Only admin can get lead counts.",
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
            message="lead count feched successfully.",
            data=result
        )
    except Exception as e:
        print("Error while counting leads:", e)
        return response(
            status="error",
            code=500,
            message="Failed to fetch lead count",
            error=str(e))

@router.post("/lead_status_history")
async def get_lead_status_history(request:Request, lead_id: int = Form(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Returns status history for a lead as an array of objects.
    Each object contains: status, Date, and By (user name)
    """
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Check if user has access to this lead
        check_query = f"SELECT assigned_to FROM {alias_name}_leads WHERE id = %s"
        cursor.execute(check_query, (lead_id,))
        lead = cursor.fetchone()
        
        if not lead:
            return response(
                status="error",
                code=404,
                message="Lead not found",
                error="Lead does not exist"
            )
        
        # Check authorization
        if role_user.lower() not in ['admin', 'hr']:
            if lead['assigned_to'] != username:
                return response(
                    status="error",
                    code=401,
                    message="You don't have access to this lead's status history",
                    error="Not authorized"
                )
        
        # Additional check: salesman, consultant, and implementation_engineer can view if assigned
        if role_user.lower() in ['salesman', 'consultant', 'implementation_engineer']:
            if lead['assigned_to'] != username:
                return response(
                    status="error",
                    code=401,
                    message="You can only view status history for leads assigned to you",
                    error="Not authorized"
                )
        
        # Get status history
        query = f"SELECT status FROM {alias_name}_leads_status WHERE id = %s"
        cursor.execute(query, (lead_id,))
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if not result or not result['status']:
            return response(
                status="success",
                code=200,
                message="No status history found for this lead",
                data=[]
            )
        
        # Parse the concatenated JSON string into array of objects
        status_string = result['status']
        status_history = []
        
        # Split by '}{", which is how multiple JSON objects are concatenated
        if status_string:
            # Handle case where multiple JSON objects are concatenated
            json_parts = []
            bracket_count = 0
            current_json = ""
            
            for char in status_string:
                current_json += char
                if char == '{':
                    bracket_count += 1
                elif char == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        try:
                            json_obj = json.loads(current_json)
                            json_parts.append(json_obj)
                        except json.JSONDecodeError:
                            pass
                        current_json = ""
            
            status_history = json_parts
        
        return response(
            status="success",
            code=200,
            message="Lead status history fetched successfully",
            data=status_history
        )
        
    except Exception as e:
        print("Error while fetching lead status history:", e)
        return response(
            status="error",
            code=500,
            message="Failed to fetch lead status history",
            error=str(e)
        )


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
                message="Invalid file format. Missing required headers.",
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
                message="Database connection failed.",
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
            message="File validated and data saved successfully!",
            data={"filename": file.filename, "records_saved": len(rows_to_insert)}
        )

    except Exception as e:
        # If anything goes wrong, roll back any changes
        if connection:
            connection.rollback()
        return response(
            status="error",
            code=500,
            message="An error occurred while processing the file.",
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
            message="Failed to generate CSV template.",
            error=str(e)
        )
from fastapi import APIRouter, Request,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db_config import get_connection
from datetime import datetime

router = APIRouter()
security = HTTPBearer()

connection = get_connection()
cursor = connection.cursor(dictionary=True)

@router.post("/lead")
async def add_lead(
    request:Request,
                name: str,
                   company_name: str,
                   city: str,
                   state: str,
                   contect_1:int,
                   inquery_type:str,
                   email: str,
                requirement: str,
                        progress: str,
                        stage: str="open",
                        next_followup:str=None,
                     status: str =None,
                        assigned_to: str= None,
                        credentials: HTTPAuthorizationCredentials = Depends(security)
                   ):
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if role_user.lower() not in ["admin","hr"]:
        return {"error":"Only admin,hr and salesman can add lead."}
    
    if stage and stage not in ("open","closed","in progress"):
        return {"message": "Invalid progress value provided. Must be 'open', 'closed', or 'in progress'."}
    if progress and progress not in ("warm","hot","cold","po raised"):
        return {"message": "Invalid progress value provided. Must be 'Warm', 'Hot', 'Cold', or 'PO Raised'."}
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = f"""
        INSERT INTO {alias_name}_leads (date, name, company_name, city, state, contact_1, inquiry_type, email, requirement, status, assigned_to, progress, stage, next_followup) VALUES (CURDATE(),%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" 
    try:

        cursor.execute(query, (name, company_name, city, state, contect_1, inquery_type, email, requirement, status, assigned_to, progress, stage, next_followup))
        connection.commit() 
        cursor.close()
        connection.close()
        return {"message": "Lead added successfully"}
    except Exception as e:
        print("Error while inserting lead details:", e)
        return {"message": "Failed to add lead"}
    

# alias_name = "tq"  # Example alias name; in practice, this would come from the request
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
async def assign_leads(request:Request, lead_id:int, assiged_to:str,credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    
    if role_user.lower() != "admin":
        return {'staus':'error',"error":"Only admin can assign lead."}
    try:
        cursor.execute(f"UPDATE {alias_name}_leads SET stage = 'in progress', assigned_to = %s WHERE id = %s", (assiged_to, lead_id))
        connection.commit()
        return {'staus':'success',"message": "leads assigned successfully"}
    except Exception as e:
        return {"error": str(e)}
    
    

@router.get("/get_leads")
async def fetch_leads(request:Request,stage:str=None,credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if stage == "all":
        stage = None
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query  = f"SELECT role FROM {alias_name}_employees WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()  
        if not result:
            return {"message": "User not found"}
        role = result['role']
        if role not in ['Admin']:
            if stage:
                query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s AND stage = %s "
                cursor.execute(query, (username,stage))
            else:
                query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s "
                cursor.execute(query, (username,))
            leads = cursor.fetchall()
            if leads is None:
                return {"message": "No leads found for the user"}
            cursor.close()
            connection.close()
            return {"leads": leads}
        
        if stage:
            query  = f"SELECT * FROM {alias_name}_leads WHERE stage = %s"
            cursor.execute(query,(stage,))
        else:
            query = f"SELECT * FROM {alias_name}_leads"
            cursor.execute(query)

        leads = cursor.fetchall()
        if leads is None:
            return {"message": "No leads found"}
        cursor.close()
        connection.close()
        return {"leads": leads}
            
    except Exception as e:
        print("Error while fetching leads:", e)
        return {"message": "Failed to fetch leads"}
    
@router.get("/filter_leads")
async def filter_leads(username:str,alias_name:str,stage:str=None ,state:str=None,city :str = None,Enquiry_type:str=None,assigned_to:str=None):
    parameters = []
    values = []
    if stage == "all":
        stage = None
    if stage and stage not in ("open","closed","in progress"):
        return {"message": "Invalid progress value provided. Must be 'open', 'closed', or 'in progress'."}
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
        query  = f"SELECT role FROM {alias_name}_employees WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()  
        if not result:
            return {"message": "User not found"}
        role = result['role']
        if role not in ['Admin',"HR"]:
            query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s "
            cursor.execute(query, (username,))
            leads = cursor.fetchall()
            if leads is None:
                return {"message": "No leads found for the user"}
            cursor.close()
            connection.close()
            return {"leads": leads}
        if len(parameters) ==0 :
            filter = ""
            query = f"SELECT * FROM {alias_name}_leads"
            cursor.execute(query)
        else:
            filter  = " AND ".join(parameters)
            query = f"SELECT * FROM {alias_name}_leads WHERE "+filter
            cursor.execute(query,tuple(values))
        print(query)
        leads = cursor.fetchall()
        if leads is None:
            return {"message": "No leads found"}
        cursor.close()
        connection.close()
        return {"leads": leads}
            
    except Exception as e:
        print("Error while fetching leads:", e)
        return {"message": "Failed to fetch leads"}
    
@router.put("/update_lead")
async def update_lead(
    request:Request,
    lead_id: int,
                   name: str,
                   company_name: str = None,
                   city: str = None,
                   state: str = None,
                   contect_1:int = None,
                   inquery_type:str = None,
                   email: str = None,
                requirement: str = None,
                     status: str    = None,
                        assigned_to: str        = None,
                        progress: str      = None,
                        stage: str     = None,
                        next_followup:str   = None,
                     credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    alias_name = request.state.user[2]
    role_user = request.state.user[1]
    if role_user.lower() not in ["admin",]:
        return {"error":"Only admin can update lead."}
    
    if stage and stage not in ("open","closed","in progress"):
        return {"message": "Invalid progress value provided. Must be 'Open', 'Closed', or 'In Progress'."}
    if progress and  progress not in ("warm","hot","cold","po raised"):
        return {"message": "Invalid progress value provided. Must be 'Warm', 'Hot','Cold', or 'PO Raised'."}
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query  = f"SELECT role FROM {alias_name}_employees WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()  
        if not result:
            return {"message": "User not found"}
        role = result['role']
        if role not in ['Admin',"HR"]:
            return {"message": "Unauthorized to update lead"}
        
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
            return {"message": "No fields to update"}
        
        params.append(lead_id)
        query = f"UPDATE {alias_name}_leads SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, tuple(params))
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "Lead updated successfully"}
    except Exception as e:
        print("Error while updating lead:", e)
        return {"message": "Failed to update lead"}

@router.put("/lead_status/{lead_id}")
async def update_lead_status(request:Request,lead_id: int, status: str,progress: str= None,credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if role_user.lower() not in ["admin","salesman"]:
        return {"error":"Only admin and salesman can update lead status."}
    
    if progress and progress not in ("warm","hot","cold","po raised"):
        return {"message": "Invalid progress value provided. Must be 'Warm', 'Hot','Cold', or 'PO Raised'."}
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
                return {"message": "Lead not found"}
            query = f"INSERT INTO {alias_name}_projects (id) VALUES (%s)"

            if lead['assigned_to'] != username and role_user != 'Admin':
                return {"message": "Unauthorized to update this lead"}
            cursor.execute(query, (lead['id'],))
            connection.commit()

        except Exception as e:
            print("Error while fetching lead details:", e)
            raise {"message": f"Failed to fetch lead details {e}"}


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
        return {"message": "Lead status updated successfully"}
    except Exception as e:
        print("Error while updating lead status:", e)
        return {"message": "Failed to update lead status"}
    
@router.delete("/lead/{lead_id}")
async def close_lead(request:Request,lead_id: int,credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if role_user not in ['Admin',"Salesman"]:
        return {"message": "Unauthorized to close lead"}
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = f"SELECT assigned_to FROM {alias_name}_leads WHERE id = %s"
    cursor.execute(query, (lead_id,))
    lead = cursor.fetchone()
    if not lead:
        return {"message": "Lead not found"
                }
    assigned_to = lead['assigned_to']
    if assigned_to != username and role_user != 'Admin':
        return {"message": "Unauthorized to close this lead"}
    try:
        query = f"UPDATE {alias_name}_leads SET stage = %s WHERE id = %s"
        cursor.execute(query, ("closed", lead_id))
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "Lead closed successfully"}
    except Exception as e:
        print("Error while closing lead:", e)
        return {"message": "Failed to close lead"}
    
@router.get("/count_leads")
async def count_leads(request:Request,credentials: HTTPAuthorizationCredentials = Depends(security)):
    alias_name = request.state.user[2]
    role_user = request.state.user[1]
    if role_user.lower() not in ["admin"]:
        return {"error":"Only admin and HR can access lead counts."}
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = f"""SELECT 
    COUNT(*) as total_leads,
    COUNT(CASE WHEN stage = 'open' THEN 1 END) as open_leads,
    COUNT(CASE WHEN stage = 'closed' THEN 1 END) as closed_leads,
    COUNT(CASE WHEN stage = 'in progress' THEN 1 END) as in_progress_leads
    FROM {alias_name}_leads"""
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result
    except Exception as e:
        print("Error while counting leads:", e)
        return {"message": f"Failed to count leads {e}"}


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
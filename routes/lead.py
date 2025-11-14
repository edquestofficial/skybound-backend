from fastapi import APIRouter,Form,Request,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db_config import get_connection
from datetime import datetime
from util.api_parameters import Leads
from util.config import response

router = APIRouter()
security = HTTPBearer()


@router.post("/lead")
async def add_lead(
    request:Request,leads:Leads,credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
    """
    This API is used to add new lead.
    Required parameters :-
        name:str,name of the lead.
        comany_name:str,
        city:str,
        state:str,
        contect:int,
        inquery_type:str
        email:str,
        requirement:str,
        progress:str,
    Optional parameters:-
        status:str,
        stage:str,
        next_followup:str,
        assigned_to:str,

    """
    
    name = leads.name
    company_name = leads.company_name
    city = leads.city
    state = leads.state
    contect_1 = leads.contect
    inquery_type = leads.inquery_type
    email = leads.email
    requirement = leads.requirement
    progress = leads.progress
    stage  = leads.stage
    next_followup = leads.next_followup
    status = leads.status
    assigned_to = leads.assigned_to
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
async def assign_leads(request:Request,leads :Leads,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """This API is used to assign lead.
    Required parameters :-
        lead_id:str,
        assigned_to:str,
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    lead_id = leads.lead_id
    assiged_to = leads.assigned_to
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
async def assign_bulk_leads(request:Request,leads:Leads,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """This API is used to bulk assign lead.
    Required parameters :-
        lead_ids:list,
        assigned_to:str,
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    lead_id = leads.lead_ids
    assiged_to = leads.assigned_to
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
    
    

@router.patch("/get_leads")
async def fetch_leads(request:Request,leads:Leads,credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    stage = leads.stage
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
    
@router.get("/filter_leads")
async def filter_leads(request:Request,leads:Leads,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    This api is used to filter leads.
    optinal parameters :-
        stage:str,
        state:str,
        city:str,
        inquery_type:str,
        assigned_to:str
    """
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    stage = leads.stage
    state = leads.state
    city = leads.city
    Enquiry_type = leads.inquery_type
    assigned_to = leads.assigned_to
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
        if role_user not in ['Admin',"HR"]:
            if len(parameters) == 0 :
                query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s "
                cursor.execute(query, (username,))
            else:
                filter  = " AND ".join(parameters)
                query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s"+filter
                cursor.execute(query,(username,).append(tuple(values)))
        else:
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
async def update_lead(request:Request,leads:Leads,credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
    """
    This API is used to update lead.
    Required parameters :-
        lead_id:int.
    Optional parameters:-
        name:str,name of the lead.
        comany_name:str,
        city:str,
        state:str,
        contect:int,
        inquery_type:str
        email:str,
        requirement:str,
        progress:str,
        status:str,
        stage:str,
        next_followup:str,
        assigned_to:str,

    """
    lead_id = leads.lead_id
    name = leads.name
    company_name = leads.company_name
    city = leads.city
    state = leads.contect_1
    contect_1 = leads.contect_1
    inquery_type = leads.inquery_type
    email = leads.email
    requirement = leads.requirement
    progress = leads.progress
    stage  = leads.stage
    next_followup = leads.next_followup
    status = leads.status
    assigned_to = leads.assigned_to

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
            message="No fields to update",
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
@router.put("/lead_status/}")
async def update_lead_status(request:Request,leads:Leads,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    This api used to update lead status.
    required parameter:
        lead_id:str,
        status:str,
    optional parameter:
        progress:str
    """
    lead_id = leads.lead_id
    status = leads.status
    progress = leads.progress
    username = request.state.user[0]
    role_user = request.state.user[1]
    alias_name = request.state.user[2]
    if role_user.lower() not in ["admin","salesman"]:
        return response(
            status="error",
            code=401,
            message="Only admin and salesman can update lead status.",
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
                    message="Lead not fount in the database",
                    error="lead not found"
                )
            query = f"INSERT INTO {alias_name}_projects (id) VALUES (%s)"

            if lead['assigned_to'] != username and role_user != 'Admin':
                return response(
            status="error",
            code=401,
            message="Only admin and assigned salesman can update lead status.",
            error="NOt authorized"
        )
            cursor.execute(query, (lead['id'],))
            connection.commit()

        except Exception as e:
            print("Error while fetching lead details:", e)
            return response(
            status="error",
            code=500,
            message="Failed to fetch lead detailsd",
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
async def close_lead(request:Request,leads:Leads,credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    this API is used to close a lead.
    required parameter:
        lead_id:int
    """
    lead_id = leads.lead_id
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
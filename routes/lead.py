from fastapi import APIRouter, Request
from db_config import get_connection
from datetime import datetime

router = APIRouter()

connection = get_connection()
cursor = connection.cursor(dictionary=True)

@router.post("/lead")
async def add_lead(
                name: str,
                   company_name: str,
                   city: str,
                   state: str,
                   contect_1:int,
                   inquery_type:str,
                   email: str,
                requirement: str,
                     status: str,
                        assigned_to: str,
                        progress: str,
                        active: bool,
                        next_followup:str,
                        alias_name:str
                   ):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = f"""
        INSERT INTO {alias_name}_leads (date, name, company_name, city, state, contact_1, inquiry_type, email, requirement, status, assigned_to, progress, active, next_followup) VALUES (CURDATE(),%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" 
    try:

        cursor.execute(query, (name, company_name, city, state, contect_1, inquery_type, email, requirement, status, assigned_to, progress, active, next_followup))
        connection.commit() 
        cursor.close()
        connection.close()
        return {"message": "Lead added successfully"}
    except Exception as e:
        print("Error while inserting lead details:", e)
        return {"message": "Failed to add lead"}
    

alias_name = "tq"  # Example alias name; in practice, this would come from the request
@router.post("/leads")
async def get_leads(request:Request):
    data = await request.json()
    id= data.get("UNIQUE_QUERY_ID")
    name = data.get("name")
    company_name = data.get("company_name")
    city = data.get("city")
    state = data.get("state")
    contect_1 = data.get("contect_1")
    inquery_type = data.get("inquery_type")
    email = data.get("email")
    requirement = data.get("requirement")
    status = data.get("status")
    assigned_to = data.get("assigned_to")
    progress = data.get("progress")
    active = data.get("active")
    next_followup = data.get("next_followup")
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = f"""
            INSERT INTO {alias_name}_leads (UNIQUE_QUERY_ID,date, name, company_name, city, state, contact_1, inquiry_type, email, requirement, status, assigned_to, progress, active, next_followup) VALUES (%s,CURDATE(),%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" 
        cursor.execute(query, (id,name, company_name, city, state, contect_1, inquery_type, email, requirement, status, assigned_to, progress, active, next_followup))
        connection.commit() 
        cursor.close()
        connection.close()
        return {"message": "Lead added successfully"}
    except Exception as e:
        return {"error": "Invalid JSON data"}

@router.get("/leads")
async def fetch_leads(username:str,alias_name:str):
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
            query = f"SELECT * FROM {alias_name}_leads WHERE assigned_to = %s"
            cursor.execute(query, (username,))
            leads = cursor.fetchall()
            if leads is None:
                return {"message": "No leads found for the user"}
            cursor.close()
            connection.close()
            return {"leads": leads}
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
    
@router.put("/lead/{lead_id}")
async def update_lead(lead_id: int,username:str,
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
                        active: bool     = None,
                        next_followup:str   = None,
                        alias_name:str = None):
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
        if active is not None:
            update_fields.append("active = %s")
            params.append(active)
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
async def update_lead_status(lead_id: int, status: str,alias_name:str,username:str,progress: str= None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query  = f"SELECT role FROM {alias_name}_employees WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()  
    if not result:
        return {"message": "User not found"}
    role = result['role']
    if role not in ['Admin',"Salesman"]:
        return {"message": "Unauthorized to update lead's status"}
    update_fields = []
    params = []
    update_fields.append("status = %s")
    params.append(status)
    if progress is not None:
        update_fields.append("progress = %s")
        params.append(progress)
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
async def close_lead(lead_id: int,alias_name:str,username:str):
    query  = f"SELECT role FROM {alias_name}_employees WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()  
    if not result:
        return {"message": "User not found"}
    role = result['role']
    if role not in ['Admin',"Salesman"]:
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
    if assigned_to != username and role != 'Admin':
        return {"message": "Unauthorized to close this lead"}
    try:
        query = f"UPDATE {alias_name}_leads SET active = %s WHERE id = %s"
        cursor.execute(query, (False, lead_id))
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "Lead closed successfully"}
    except Exception as e:
        print("Error while closing lead:", e)
        return {"message": "Failed to close lead"}
    
@router.get("/count_leads")
async def count_leads(alias_name:str, username:str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    return {"total_leads": 100,
            "active_leads": 80,
            "closed_leads": 20,
            "assinged_leads": 50,
            "unassinged_leads": 50,
            "hot_leads": 30,
            "cold_leads": 20,
            "warm_leads": 50}
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
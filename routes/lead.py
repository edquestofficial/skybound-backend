from fastapi import APIRouter, Request
from db_config import get_connection
from datetime import datetime

router = APIRouter()

connection = get_connection()
cursor = connection.cursor(dictionary=True)

# @router.post("/lead")
# async def add_lead(
#                 name: str,
#                    company_name: str,
#                    city: str,
#                    state: str,
#                    contect_1:int,
#                    inquery_type:str,
#                    email: str,
#                 requirement: str,
#                      status: str,
#                         assigned_to: str,
#                         progress: str,
#                         active: bool,
#                         next_followup:str,
#                         alias_name:str
#                    ):
#     connection = get_connection()
#     cursor = connection.cursor(dictionary=True)
#     query = f"""
#         INSERT INTO {alias_name}_leads (date, name, company_name, city, state, contact_1, inquiry_type, email, requirement, status, assigned_to, progress, active, next_followup) VALUES (CURDATE(),%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" 
#     try:

#         cursor.execute(query, (name, company_name, city, state, contect_1, inquery_type, email, requirement, status, assigned_to, progress, active, next_followup))
#         connection.commit() 
#         cursor.close()
#         connection.close()
#         return {"message": "Lead added successfully"}
#     except Exception as e:
#         print("Error while inserting lead details:", e)
#         return {"message": "Failed to add lead"}
    

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

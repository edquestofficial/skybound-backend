from fastapi import APIRouter, Request
from db_config import get_connection
from datetime import datetime

router = APIRouter()

connection = get_connection()
cursor = connection.cursor(dictionary=True)

@router.put("/assign_project")
async def assign_project(username:str,company_alise:str, project_id:int, assiged_to:str):
    table_name = f"{company_alise}_projects"
    try:
        cursor.execute(f"UPDATE {table_name} SET assigned_to = %s WHERE id = %s", (assiged_to, project_id))
        connection.commit()
        return {"message": "Project assigned successfully"}
    except Exception as e:
        return {"error": str(e)}
    
@router.put("/update_project_status")
async def update_project_status(username:str,company_alise:str, project_id:int, status:str):
    table_name = f"{company_alise}_projects"
    try:
        cursor.execute(f"UPDATE {table_name} SET status = %s WHERE id = %s", (status, project_id))
        connection.commit()
        return {"message": "Project status updated successfully"}
    except Exception as e:
        return {"error": str(e)}
    
@router.put("/raise_review_request")
async def raise_review_request(username:str,alias_name:str, project_id:int):
    table_name = f"{alias_name}_projects"
    try:

        query  = f"SELECT * FROM {table_name} WHERE id = %s"
        cursor.execute(query, (project_id,))
        result = cursor.fetchone()  
        if not result:
            return {"message": "User not found"}
        assigned_to = result['assigned_to']
        if assigned_to != username:
            return {"message": "Unauthorized to update lead"}

        cursor.execute(f"UPDATE {table_name} SET progress = %s WHERE id = %s", ("raised review", project_id))
        connection.commit()
        return {"message": "Review request raised successfully"}
    except Exception as e:
        return {"error": str(e)}
    
@router.delete("/close_project")
async def close_project(username:str,alias_name:str, project_id:int):
    table_name = f"{alias_name}_projects"
    try:
        query  = f"SELECT role FROM {alias_name}_employees WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()  
        if not result:
            return {"message": "User not found"}
        role = result['role']
        if role not in ['Admin',"HR"]:
            return {"message": "Unauthorized to update lead"}
        
        cursor.execute(f"UPDATE {table_name} SET progress = %s,active = %s  WHERE id = %s", ("closed",False, project_id))
        connection.commit()
        return {"message": "Project closed successfully"}
    except Exception as e:
        return {"error": str(e)}
    
@router.get("/projects")
async def get_projects(username:str,alias_name:str,assigned_to: bool,progress: str = None,active: bool = True):
    table_name = f"{alias_name}_projects"
    parameters = []
    values = []

    if assigned_to:
        parameters.append(f"{table_name}.assigned_to IS %s")
        values.append(None)
    elif not assigned_to:
        parameters.append(f"{table_name}.assigned_to IS NOT %s")
        values.append(None)
    if progress:
        parameters.append(f"{table_name}.progress = %s")
        values.append(progress)
    if active is not None:
        parameters.append(f"{table_name}.active = %s")
        values.append(active)
    filter  = " AND ".join(parameters)
    try:
        query  = f"SELECT role FROM {alias_name}_employees WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()  
        if not result:
            return {"message": "User not found"}
        role = result['role']
        if role in ['Admin',"HR"]:
            cursor.execute(f"SELECT {table_name}.*,{alias_name}_leads.UNIQUE_QUERY_ID,{alias_name}_leads.name,{alias_name}_leads.company_name,{alias_name}_leads.city,{alias_name}_leads.state,{alias_name}_leads.contact_1,{alias_name}_leads.inquiry_type,{alias_name}_leads.requirement FROM {table_name} LEFT JOIN {alias_name}_leads ON {table_name}.id = {alias_name}_leads.id WHERE {filter}", tuple(values))
        else:
            cursor.execute(f"SELECT {table_name}.*,{alias_name}_leads.UNIQUE_QUERY_ID,{alias_name}_leads.name,{alias_name}_leads.company_name,{alias_name}_leads.city,{alias_name}_leads.state,{alias_name}_leads.contact_1,{alias_name}_leads.inquiry_type,{alias_name}_leads.requirement FROM {table_name} LEFT JOIN {alias_name}_leads ON {table_name}.id = {alias_name}_leads.id WHERE {table_name}.assigned_to = %s AND {table_name}active = %s", (username,True))
        projects = cursor.fetchall()
        return {"projects": projects}
    except Exception as e:
        return {"error": str(e)}
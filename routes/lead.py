from fastapi import APIRouter, HTTPException,Depends
from schemas.lead import Lead
from database import execute_company_query, execute_query,fetch_single_record

from core.config import  db_query
from models.response import response
from core.role import Role
from utility.auth import role_required

lead_router = APIRouter()



@lead_router.post("/create")
def create(lead: Lead,userinfo = Depends(role_required([Role.Admin]))):
    
    execute_company_query(db_query['LEAD']['INSERT'],lead.name, lead.company_name,lead.city,lead.state,lead.contact,lead.enquery_type,lead.email,lead.requirement,lead.progress,lead.stage,lead.next_followup,lead.status,lead.assigned_to,"",1,userinfo.id)
    return response(
            status="success",
            code=200,
            message="Lead created successfully",
            data=[]
        )

@lead_router.get("/")
def fetch_all(userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    if userinfo.role == Role.Sales:
        result =  execute_company_query(db_query['LEAD']['SELECT_BY_USER'],userinfo.id)
    else:
        result =  execute_company_query(db_query['LEAD']['SELECT_ALL'])
    return response(
            status="success",
            code=200,
            message="Lead fetch successfully",
            data=result
        )

    
@lead_router.get("/userid/{id}")
def fetch_by_user(id :str,userid = Depends(role_required([Role.Admin,Role.Sales]))):
    
    result =  execute_company_query(db_query['LEAD']['SELECT_BY_USER'],id)
    return response(
            status="success",
            code=200,
            message="Lead fetch successfully",
            data=result
        )
@lead_router.get("/{lead_id}")
def fetch_by_leadid(lead_id :int,userid = Depends(role_required([Role.Admin,Role.Sales]))):
    
    result =  execute_company_query(db_query['LEAD']['SELECT_BY_LEADID'],lead_id)
    return response(
            status="success",
            code=200,
            message="Lead fetch successfully",
            data=result
        )

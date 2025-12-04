from fastapi import APIRouter, HTTPException,Depends
from schemas.lead import Lead, EditLead
from database import execute_company_query, execute_query,fetch_single_record

from core.config import  db_query
from models.response import response
from core.role import Role
from utility.auth import role_required
from services.lead import updateLead

lead_router = APIRouter()



@lead_router.post("/create")
def create(lead: Lead,userinfo = Depends(role_required([Role.Admin]))):
    
    execute_company_query(db_query['LEAD']['INSERT'],lead.name, lead.company_name,lead.city,lead.state,lead.contact_number,lead.enquery_type,lead.email,lead.requirement,1,'open',userinfo['id'])
    return response(
            status="success",
            code=200,
            message="Lead created successfully",
            data=[]
        )


@lead_router.get("/")
def fetch(userId:str = "", leadId:str="", userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    loggedin_user_id = int(userinfo['id'])
    if int(userinfo['role']) == Role.Admin.value:
        if userId != "" and leadId == "" :
          result =  execute_company_query(db_query['LEAD']['SELECT_BY_USER'],int(userId))
        elif leadId !="":
            result =  execute_company_query(db_query['LEAD']['SELECT_BY_LEADID'],int(leadId))
        elif userId == "" and leadId == "" :
             result =  execute_company_query(db_query['LEAD']['SELECT_ALL'])
    elif int(userinfo['role']) == Role.Sales.value:
        if leadId !="":
            result =  execute_company_query(db_query['LEAD']['SELECT_BY_LEADID_ASSIGN'],int(leadId),loggedin_user_id)
        else:
            result =  execute_company_query(db_query['LEAD']['UNASSIGN_ASSIGN_LEAD'],loggedin_user_id)

    return response(
            status="success",
            code=200,
            message="Lead fetch successfully",
            data=result
        )

@lead_router.patch("/{id}")
def edit(id:int, update:EditLead, userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
     loggedin_userId = userinfo['id']
     if updateLead(id,update, loggedin_userId):
         return response(
            status="success",
            code=200,
            message="Lead update successfully",
            data=[]
        )
     else:
          raise HTTPException(401, "Error in update Lead")
   


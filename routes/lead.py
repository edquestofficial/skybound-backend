from fastapi import APIRouter, HTTPException,Depends
from schemas.lead import Lead, EditLead, SearchLead

from models.response import Response
from core.role import Role
from utility.auth import role_required
from services.lead import create_lead, updateLead, count_lead, fetch_lead, addTimeLine

lead_router = APIRouter()


@lead_router.post("/create")
def create(lead: Lead,userinfo = Depends(role_required([Role.Admin]))):
    create_lead(lead,userinfo)
    return Response(
            status="success",
            code=200,
            message="Lead created successfully",
            data=[]
        )


@lead_router.post("/")
def fetch( lead :SearchLead, userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
   
    result = fetch_lead(lead,userinfo)
    return Response(
            status="success",
            code=200,
            message="Lead fetch successfully",
            data=result
        )





@lead_router.patch("/{id}")
def edit(id:int, update:EditLead, userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
     loggedin_userId = userinfo['id']
     if updateLead(id,update, loggedin_userId):
         return Response(
            status="success",
            code=200,
            message="Lead update successfully",
            data=[]
        )
     else:
          raise HTTPException(401, "Error in update Lead")
   
@lead_router.get("/count")
def dashboardCount( userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    result = count_lead(userinfo)
    return Response(
            status="success",
            code=200,
            message="Fetch Count successfully",
            data=result
        )

@lead_router.post("/timeline")
def create(leadId:int,comment:str,docUrls:str = "",userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    addTimeLine(leadId, comment, userinfo, docUrls)
    return Response(
            status="success",
            code=200,
            message="Comment added successfully",
            data=[]
        )


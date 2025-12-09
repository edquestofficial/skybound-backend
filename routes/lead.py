import os
import shutil
from typing import List
from fastapi import APIRouter, File, Form, HTTPException,Depends, UploadFile
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

@lead_router.post("/edit")
def edit(update:EditLead, userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    
    if len(update.id) == 0:
        return Response(
            status="fail",
            code=400,
            message="please provide the atleast one lead id",
            data=[]
        )
    else:
        ids = update.id
        del update.id
        for id in ids:
            loggedin_userId = userinfo['id']
            updateLead(id,update, loggedin_userId)
    return Response(
            status="success",
            code=200,
            message="Lead update successfully",
            data=[]
                )   
   
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
def create( id: int = Form(...),
    comment: str = Form(...),
    files: List[UploadFile] = File(None),userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    saved_files = []
    docs :str = ""
    if files:
        upload_dir = "Lead_Doc"
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            file_location = f"{upload_dir}/{id}_{file.filename}"
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file_location)
            docs = ",".join(saved_files)
    addTimeLine(id, comment, userinfo, docs)
    return Response(
            status="success",
            code=200,
            message="Comment added successfully",
            data=[]
        )


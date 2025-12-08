
import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from core.role import Role
from utility.auth import role_required
from models.response import Response
from services.project import create_project,fetch_project, count_project, addTimeLine, updateProject
from schemas.project import SearchProject
project_router = APIRouter()


# @project_router.post("/create")
# def create(leadid:int, userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
#     create_project(leadid, userinfo)
#     return Response(
#                 status="success",
#                 code=200,
#                 message="Project created successfully",
#                 data=[]
#             )

@project_router.post("/")
def fetch(proj : SearchProject, userinfo = Depends(role_required([Role.Admin, Role.Engineer]))):
    result = fetch_project(proj,userinfo)
    return Response(
            status="success",
            code=200,
            message="Project fetch successfully",
            data=result
        )

@project_router.get("/count")
def dashboardCount( userinfo = Depends(role_required([Role.Admin, Role.Engineer]))):
    result = count_project(userinfo)
    return Response(
            status="success",
            code=200,
            message="Fetch Count successfully",
            data=result
        )

@project_router.patch("/{id}")
def edit(id:int, update:SearchProject, userinfo = Depends(role_required([Role.Admin, Role.Engineer]))):
     loggedin_userId = userinfo['id']
     if updateProject(id,update, loggedin_userId):
         return Response(
            status="success",
            code=200,
            message="Project update successfully",
            data=[]
        )
     else:
          raise HTTPException(401, "Error in update project")
   

@project_router.post("/timeline")
def create( id: int = Form(...),
    comment: str = Form(...),
    files: List[UploadFile] = File(None),userinfo = Depends(role_required([Role.Admin, Role.Engineer]))):
    saved_files = []
    docs :str = ""
    if files:
        upload_dir = "Project_Doc"
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
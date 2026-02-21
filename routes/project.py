import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from core.role import Role
from utility.auth import role_required
from models.response import Response
from services.project import fetch_project, count_project, addTimeLine, updateProject, editTimeLine, deleteTimeline
from schemas.project import SearchProject, UpdateModel

project_router = APIRouter()

@project_router.post("/")
def fetch(proj : SearchProject, userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead]))):
    result = fetch_project(proj,userinfo)
    return Response(
            status=True,
            code=200,
            message="Project fetch successfully",
            data=result
        )

@project_router.get("/count")
def dashboardCount( userinfo = Depends(role_required([Role.Admin, Role.Engineer , Role.EngineerHead]))):
    result = count_project(userinfo)
    return Response(
            status=True,
            code=200,
            message="Fetch count successfully",
            data=result
        )

@project_router.post("/edit")
def edit(update: UpdateModel, userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead]))):
    if len(update.id) == 0:
        return Response(
            status=False,
            code=400,
            message="Please provide at least one project ID",
        )

    if len(update.assigned_to) == 0:
        return Response(
            status=False,
            code=400,
            message="Please assign at least one user to the project",
        )

    result = updateProject(update.id[0], update, userinfo['id'])
    if result:
        return Response(
            status=True,
            code=200,
            message="Project updated successfully",
        )
    else:
        return Response(
            status=False,
            code=500,
            message="Failed to update the project",
        )
@project_router.post("/timeline")
def create_timeline( proj_id: int = Form(...),
    comment: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead]))):
    saved_files = []
    id = proj_id
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
    if files  or comment :
         addTimeLine(id, comment, userinfo, docs)
    return Response(
            status=True,
            code=200,
            message="Comment added successfully",
            data=[]
        )
@project_router.post("/timelineEdit")
def edit_timeline(id: int = Form(...), docs_urls :str = Form(...), comment: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead]))):
    saved_files = []
   
    if files:
        upload_dir = "Project_Doc"
        os.makedirs(upload_dir, exist_ok=True)
        if docs_urls and docs_urls[-1] != ",":
            docs_urls += ","
        for file in files:
            file_location = f"{upload_dir}/{id}_{file.filename}"
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file_location)
        docs_urls += ",".join(saved_files)
    
    if files  or comment :
        editTimeLine(id, comment, userinfo, docs_urls)
    return Response(
            status=True,
            code=200,
            message="Timeline edited successfully",
            data=[]
        )

@project_router.get("/timelineDelete")
def delete_timeline(id: int, userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead]))):
    result = deleteTimeline(id, userinfo)
    if result:
        return Response(
            status=True,
            code=200,
            message="Timeline deleted successfully",
            data=[]
        )
    else:
        return Response(
            status=False,
            code=400,
            message="Something went wrong !!",
            data=[] 
        )
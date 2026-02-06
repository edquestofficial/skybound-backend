
import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from core.role import Role
from utility.auth import role_required
from models.response import Response
from services.project import create_project,fetch_project, count_project, addTimeLine, updateProject
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
            message="Fetch Count successfully",
            data=result
        )

@project_router.post("/edit")
def edit(update:UpdateModel, userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead]))):
    if len(update.id) == 0:
        return Response(
            status=False,
            code=400,
            message="please provide the atleast one lead id",
            data=[]
        )
    else:
        ids = update.id
        del update.id
        for id in ids:
            loggedin_userId = userinfo['id']
            updateProject(id,update, loggedin_userId)
     
    return Response(
            status=True,
            code=200,
            message="Project update successfully",
            data=[]
        )
@project_router.post("/timeline")
def create( id: int = Form(...),
    comment: str = Form(...),
    files: List[UploadFile] = File(None),userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead]))):
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
            status=True,
            code=200,
            message="Comment added successfully",
            data=[]
        )
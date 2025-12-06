
from fastapi import APIRouter, Depends
from core.role import Role
from utility.auth import role_required
from models.response import Response
from services.project import create_project,fetch_project, count_project, addTimeLine

project_router = APIRouter()


@project_router.post("/create")
def create(leadid:int, userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    create_project(leadid, userinfo)
    return Response(
                status="success",
                code=200,
                message="Project created successfully",
                data=[]
            )

@project_router.get("/")
def fetch(userId:str = "", projid:str="", userinfo = Depends(role_required([Role.Admin, Role.Engineer]))):
    result = fetch_project(userId,projid,userinfo)
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

@project_router.post("/timeline")
def create(projid:int,comment:str,docUrls:str = None,userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    addTimeLine(projid, comment, userinfo, docUrls)
    return Response(
            status="success",
            code=200,
            message="Comment added successfully",
            data=[]
        )



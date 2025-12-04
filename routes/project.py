
from fastapi import APIRouter, Depends
from core.role import Role
from utility.auth import role_required
from models.response import response
from services.project import create_project,fetch_project

project_router = APIRouter()


@project_router.post("/create")
def create(leadid:int, userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    create_project(leadid, userinfo)
    return response(
                status="success",
                code=200,
                message="Project created successfully",
                data=[]
            )

@project_router.get("/")
def fetch(userId:str = "", projid:str="", userinfo = Depends(role_required([Role.Admin, Role.Engineer]))):
    result = fetch_project(userId,projid,userinfo)
    return response(
            status="success",
            code=200,
            message="Project fetch successfully",
            data=result
        )



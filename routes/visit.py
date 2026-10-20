from fastapi import APIRouter, Depends

from core.role import Role
from models.response import Response
from schemas.visit import CreateVisit
from services.visit import create_visit, fetch_visits
from utility.auth import role_required


visit_router = APIRouter()


@visit_router.get("/")
def get_visits(
    userinfo=Depends(role_required([Role.Sales, Role.SalesHead, Role.Admin])),
):
    result = fetch_visits(userinfo)
    return Response(
        status=True,
        code=200,
        message="Visits fetched successfully",
        data=result,
    )


@visit_router.post("/")
def create(
    visit: CreateVisit,
    userinfo=Depends(role_required([Role.Sales])),
):
    result = create_visit(visit, userinfo)
    return Response(
        status=True,
        code=200,
        message="Visit saved successfully",
        data=result,
    )

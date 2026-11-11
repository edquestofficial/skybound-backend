from fastapi import APIRouter, Depends, HTTPException

from core.role import Role
from models.response import Response
from schemas.visit import CreateVisit
from services.visit import create_visit, fetch_visits
from utility.auth import role_required
from utility.statemgmt import state


visit_router = APIRouter()


def _require_company_context(userinfo):
    if not userinfo.get("company_code") and not state.value:
        raise HTTPException(
            status_code=401,
            detail="Company context is missing. Please sign in again.",
        )


@visit_router.get("/")
def get_visits(
    userinfo=Depends(role_required([Role.Sales, Role.SalesHead, Role.Admin])),
):
    # _require_company_context(userinfo)
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
    # _require_company_context(userinfo)
    result = create_visit(visit, userinfo)
    return Response(
        status=True,
        code=200,
        message="Visit saved successfully",
        data=result,
    )

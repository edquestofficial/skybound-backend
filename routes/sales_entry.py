from fastapi import APIRouter, Depends

from core.role import Role
from models.response import Response
from schemas.sales_entry import CreateSalesEntry
from services.sales_entry import create_sales_entry, fetch_sales_entries
from utility.auth import role_required


sales_entry_router = APIRouter()


@sales_entry_router.get("/")
def get_sales_entries(
    userinfo=Depends(role_required([Role.Sales, Role.SalesHead, Role.Admin])),
):
    result = fetch_sales_entries(userinfo)
    return Response(
        status=True,
        code=200,
        message="Sales entries fetched successfully",
        data=result,
    )


@sales_entry_router.post("/")
def add_sales_entry(
    entry: CreateSalesEntry,
    userinfo=Depends(role_required([Role.Sales])),
):
    result = create_sales_entry(entry, userinfo)
    return Response(
        status=True,
        code=200,
        message="Sales entry saved successfully",
        data=result,
    )

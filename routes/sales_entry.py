from fastapi import APIRouter, Depends, HTTPException, Query

from core.role import Role
from models.response import Response
from schemas.sales_entry import CreateSalesEntry, SetAnnualSalary, SetMonthlyTarget
from services.sales_entry import (
    calculate_sales_incentive,
    create_sales_entry,
    fetch_sales_entries,
    set_annual_salary,
    set_monthly_target,
)
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


@sales_entry_router.post("/targets")
def save_monthly_target(
    target: SetMonthlyTarget,
    userinfo=Depends(role_required([Role.SalesHead, Role.Admin, Role.HR])),
):
    result = set_monthly_target(target)
    return Response(
        status=True,
        code=200,
        message="Monthly sales target saved successfully",
        data=result,
    )


@sales_entry_router.post("/annual-salaries")
def save_annual_salary(
    salary: SetAnnualSalary,
    userinfo=Depends(role_required([Role.Admin, Role.HR])),
):
    result = set_annual_salary(salary)
    return Response(
        status=True,
        code=200,
        message="Annual salary saved successfully",
        data=result,
    )


@sales_entry_router.get("/incentive")
def get_sales_incentive(
    user_id: int = Query(gt=0),
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000, le=9999),
    userinfo=Depends(
        role_required([Role.Sales, Role.SalesHead, Role.Admin, Role.HR])
    ),
):
    if (
        userinfo["role"] == Role.Sales.value
        and int(userinfo["id"]) != user_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Sales users can only view their own incentive",
        )

    result = calculate_sales_incentive(user_id, month, year)
    return Response(
        status=True,
        code=200,
        message="Sales incentive calculated successfully",
        data=result,
    )

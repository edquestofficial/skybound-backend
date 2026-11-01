from datetime import datetime

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
    entry_date: str | None = Query(
        default=None,
        alias="date",
        description="Date in DD-MM-YYYY or YYYY-MM-DD format",
    ),
    week: int | None = Query(default=None, ge=1, le=53),
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=1, le=9999),
    userinfo=Depends(role_required([Role.Sales, Role.SalesHead, Role.Admin])),
):
    parsed_date = None
    if entry_date is not None:
        for date_format in ("%d-%m-%Y", "%Y-%m-%d"):
            try:
                parsed_date = datetime.strptime(entry_date, date_format).date()
                break
            except ValueError:
                continue
        if parsed_date is None:
            raise HTTPException(
                status_code=422,
                detail="Date must be a valid date in DD-MM-YYYY or YYYY-MM-DD format",
            )

    result = fetch_sales_entries(userinfo, parsed_date, week, month, year)
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

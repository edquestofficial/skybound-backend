from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException

from core.config import db_query
from core.role import Role
from database import create_table, execute_company_query, execute_insert_query
from utility.dateutility import ist_now


_CENT = Decimal("0.01")


def create_sales_entry(entry, userinfo):
    create_table(db_query["SALES_ENTRY"]["CREATE"])
    entry_id = execute_insert_query(
        db_query["SALES_ENTRY"]["INSERT"],
        str(entry.quotation_sent_amount),
        str(entry.po_received_amount),
        str(entry.po_expected_tomorrow_amount),
        str(entry.po_expected_this_week_amount),
        userinfo["id"],
    )
    return {"sales_entry_id": entry_id, "entry_date": ist_now().split(" ")[0]}


def fetch_sales_entries(userinfo):
    create_table(db_query["SALES_ENTRY"]["CREATE"])
    sales_user_id = (
        userinfo["id"]
        if userinfo["role"] == Role.Sales.value
        else None
    )
    return execute_company_query(
        db_query["SALES_ENTRY"]["SELECT_ALL"],
        sales_user_id,
        sales_user_id,
    )


def _create_incentive_tables():
    create_table(db_query["INCENTIVE"]["CREATE_MONTHLY_TARGET"])
    create_table(db_query["INCENTIVE"]["CREATE_ANNUAL_SALARY"])


def _require_salesperson(user_id):
    rows = execute_company_query(
        db_query["INCENTIVE"]["SELECT_SALESPERSON"],
        user_id,
        Role.Sales.value,
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Salesperson not found",
        )
    return rows[0]


def set_monthly_target(target):
    _create_incentive_tables()
    salesperson = _require_salesperson(target.user_id)
    execute_company_query(
        db_query["INCENTIVE"]["UPSERT_MONTHLY_TARGET"],
        target.user_id,
        target.month,
        target.year,
        str(target.target_amount),
    )
    return {
        "user_id": target.user_id,
        "salesperson_name": salesperson["name"],
        "month": target.month,
        "year": target.year,
        "target_amount": float(target.target_amount),
    }


def set_annual_salary(salary):
    _create_incentive_tables()
    salesperson = _require_salesperson(salary.user_id)
    execute_company_query(
        db_query["INCENTIVE"]["UPSERT_ANNUAL_SALARY"],
        salary.user_id,
        salary.year,
        str(salary.annual_salary),
    )
    return {
        "user_id": salary.user_id,
        "salesperson_name": salesperson["name"],
        "year": salary.year,
        "annual_salary": float(salary.annual_salary),
    }


def calculate_sales_incentive(user_id, month, year):
    _create_incentive_tables()
    salesperson = _require_salesperson(user_id)

    targets = execute_company_query(
        db_query["INCENTIVE"]["SELECT_MONTHLY_TARGET"],
        user_id,
        month,
        year,
    )
    if not targets:
        raise HTTPException(
            status_code=404,
            detail="Monthly sales target not found",
        )

    salaries = execute_company_query(
        db_query["INCENTIVE"]["SELECT_ANNUAL_SALARY"],
        user_id,
        year,
    )
    if not salaries:
        raise HTTPException(
            status_code=404,
            detail="Annual salary not found",
        )

    sales_rows = execute_company_query(
        db_query["INCENTIVE"]["SUM_MONTHLY_PO_RECEIVED"],
        user_id,
        f"{year:04d}-{month:02d}",
    )
    sales_amount = Decimal(str(sales_rows[0]["sales_amount"]))
    target_amount = Decimal(str(targets[0]["target_amount"]))
    annual_salary = Decimal(str(salaries[0]["annual_salary"]))
    monthly_salary = (annual_salary / Decimal(12)).quantize(
        _CENT,
        rounding=ROUND_HALF_UP,
    )
    achievement_percentage = sales_amount * Decimal(100) / target_amount
    incentive_amount = (monthly_salary * sales_amount / target_amount).quantize(
        _CENT,
        rounding=ROUND_HALF_UP,
    )

    return {
        "user_id": user_id,
        "salesperson_name": salesperson["name"],
        "month": month,
        "year": year,
        "sales_amount": float(sales_amount),
        "target_amount": float(target_amount),
        "achievement_percentage": float(
            achievement_percentage.quantize(_CENT, rounding=ROUND_HALF_UP)
        ),
        "annual_salary": float(annual_salary),
        "monthly_salary": float(monthly_salary),
        "incentive_amount": float(incentive_amount),
        "total_monthly_pay": float(monthly_salary + incentive_amount),
    }

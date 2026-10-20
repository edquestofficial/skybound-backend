from core.config import db_query
from core.role import Role
from database import create_table, execute_company_query, execute_insert_query


def create_visit(visit, userinfo):
    create_table(db_query["VISIT"]["CREATE"])
    visit_id = execute_insert_query(
        db_query["VISIT"]["INSERT"],
        visit.visit_date.isoformat(),
        visit.visit_location,
        visit.contacted_person,
        visit.designation,
        visit.outcome,
        visit.remark,
        userinfo["id"],
    )
    return {"visit_id": visit_id}


def fetch_visits(userinfo):
    create_table(db_query["VISIT"]["CREATE"])
    sales_user_id = (
        userinfo["id"]
        if userinfo["role"] == Role.Sales.value
        else None
    )
    return execute_company_query(
        db_query["VISIT"]["SELECT_ALL"],
        sales_user_id,
        sales_user_id,
    )

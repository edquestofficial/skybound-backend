import json

from core.config import db_query
from core.role import Role
from database import execute_company_query, execute_insert_query


def create_visit(visit, userinfo):
    visit_id = execute_insert_query(
        db_query["VISIT"]["INSERT"],
        visit.visit_date.isoformat(),
        visit.state,
        visit.city,
        visit.location.model_dump_json(),
        visit.contacted_person,
        visit.designation,
        visit.outcome,
        visit.remark,
        userinfo["id"],
    )
    return {"visit_id": visit_id}


def fetch_visits(userinfo):
    sales_user_id = (
        userinfo["id"]
        if userinfo["role"] == Role.Sales.value
        else None
    )
    visits = execute_company_query(
        db_query["VISIT"]["SELECT_ALL"],
        sales_user_id,
        sales_user_id,
    )
    for visit in visits:
        try:
            visit["location"] = json.loads(visit["location"])
        except json.JSONDecodeError:
            visit["location"] = {
                "latitude": None,
                "longitude": None,
                "address": visit["location"],
            }
    return visits

import json
import re

from core.config import db_query
from core.role import Role
from database import create_table, execute_company_query, execute_insert_query, get_db
from utility.statemgmt import state


def ensure_visit_schema():
    create_table(db_query["VISIT"]["CREATE"])
    table_name = f'{state.value}_visit'.replace('"', '""')
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        columns = {
            row["name"] for row in conn.execute(f'PRAGMA table_info("{table_name}")')
        }
        if "address" not in columns:
            conn.execute(
                f'ALTER TABLE "{table_name}" ADD COLUMN "address" TEXT NOT NULL DEFAULT \'\''
            )
        table_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name.replace('""', '"'),),
        ).fetchone()["sql"]
        outcome_check = re.compile(
            r"CHECK\s*\(\s*outcome\s+IN\s*\([^)]*\)\s*\)", re.IGNORECASE
        )
        check_match = outcome_check.search(table_sql)
        if check_match and "'Negative'" not in check_match.group():
            temporary_table_name = f"{state.value}_visit_migration"
            conn.execute(f'DROP TABLE IF EXISTS "{temporary_table_name}"')
            create_sql = outcome_check.sub(
                "CHECK(outcome IN ('Positive', 'Follow-up', 'Negative', 'Not Interested'))",
                table_sql,
                count=1,
            )
            create_sql = create_sql.replace(
                f"{state.value}_visit", temporary_table_name, 1
            )
            conn.execute(create_sql)
            columns = [
                row["name"] for row in conn.execute(f'PRAGMA table_info("{table_name}")')
            ]
            column_list = ", ".join(f'"{column}"' for column in columns)
            conn.execute(
                f'INSERT INTO "{temporary_table_name}" ({column_list}) '
                f'SELECT {column_list} FROM "{table_name}"'
            )
            conn.execute(f'DROP TABLE "{table_name}"')
            conn.execute(
                f'ALTER TABLE "{temporary_table_name}" RENAME TO "{table_name}"'
            )
        conn.commit()
    finally:
        conn.close()


def create_visit(visit, userinfo):
    ensure_visit_schema()
    visit_id = execute_insert_query(
        db_query["VISIT"]["INSERT"],
        visit.visit_date.isoformat(),
        visit.state,
        visit.city,
        visit.location.model_dump_json(),
        visit.address,
        visit.contacted_person,
        visit.designation,
        visit.outcome,
        visit.remark,
        userinfo["id"],
    )
    return {"visit_id": visit_id}


def fetch_visits(userinfo):
    ensure_visit_schema()
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
        saved_address = visit.get("address")
        try:
            location = json.loads(visit["location"])
        except json.JSONDecodeError:
            location = None
        if isinstance(location, dict):
            visit["address"] = saved_address or location.pop("address", None)
            visit["location"] = {
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
            }
        else:
            visit["address"] = saved_address or visit["location"]
            visit["location"] = {"latitude": None, "longitude": None}
    return visits

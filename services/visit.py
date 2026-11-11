import json
import re

from core.config import db_query
from core.role import Role
from database import get_db
from utility.statemgmt import state


def _company_alias(userinfo):
    company_alias = userinfo.get("company_code") or state.value
    if not company_alias:
        raise ValueError("Company code is missing from the authenticated user")
    return company_alias


def _quoted_identifier(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def _visit_query(query, company_alias):
    return query.replace(
        "<>_visit", _quoted_identifier(f"{company_alias}_visit")
    ).replace(
        "<>_user", _quoted_identifier(f"{company_alias}_user")
    )


def ensure_visit_schema(company_alias):
    table_name = f'{company_alias}_visit'.replace('"', '""')
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            db_query["VISIT"]["CREATE"].replace(
                "<>_visit", _quoted_identifier(f"{company_alias}_visit")
            )
        )
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
        ).fetchone()
        if table_sql is None:
            raise RuntimeError(f"Visit table {table_name!r} was not created")
        table_sql = table_sql["sql"]
        outcome_check = re.compile(
            r"CHECK\s*\(\s*outcome\s+IN\s*\([^)]*\)\s*\)", re.IGNORECASE
        )
        check_match = outcome_check.search(table_sql)
        if check_match and "'Negative'" not in check_match.group():
            temporary_table_name = f"{company_alias}_visit_migration"
            conn.execute(f'DROP TABLE IF EXISTS "{temporary_table_name}"')
            create_sql = outcome_check.sub(
                "CHECK(outcome IN ('Positive', 'Follow-up', 'Negative', 'Not Interested'))",
                table_sql,
                count=1,
            )
            create_sql = create_sql.replace(
                f"{company_alias}_visit", temporary_table_name, 1
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
    company_alias = _company_alias(userinfo)
    ensure_visit_schema(company_alias)
    conn = get_db()
    try:
        cursor = conn.execute(
            _visit_query(db_query["VISIT"]["INSERT"], company_alias),
            (
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
            ),
        )
        conn.commit()
        visit_id = cursor.lastrowid
    finally:
        conn.close()
    return {"visit_id": visit_id}


def fetch_visits(userinfo):
    company_alias = _company_alias(userinfo)
    ensure_visit_schema(company_alias)
    sales_user_id = (
        userinfo["id"]
        if userinfo["role"] == Role.Sales.value
        else None
    )
    conn = get_db()
    try:
        visits = [
            dict(row)
            for row in conn.execute(
                _visit_query(db_query["VISIT"]["SELECT_ALL"], company_alias),
                (sales_user_id, sales_user_id),
            ).fetchall()
        ]
    finally:
        conn.close()
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

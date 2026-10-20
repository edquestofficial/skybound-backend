from core.config import db_query
from core.role import Role
from database import create_table, execute_company_query, execute_insert_query
from utility.dateutility import ist_now


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

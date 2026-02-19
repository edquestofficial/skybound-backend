from core.role import Role
from database import execute_company_query
from core.config import db_query
from utility.pushnotify import send_notifications

def addTimeLine(comment, userinfo, docUrls):
    device_tokens = []
    result = execute_company_query(db_query['COMPANY_TIMELINE']['INSERT'],comment,docUrls,userinfo['id'])
    if result:
        query = db_query["USER"]["SELECT_SALESPERSON_DEVICE_TOKEN"]
        rows= execute_company_query( query, Role.EngineerHead.value, Role.Admin.value, Role.SalesHead.value)
        device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
   
    # send notification to all sales person
    if device_tokens:
        title = "Company timeline updated"
        message = f"A Company timeline has been added."
        send_notifications(device_tokens, title, message)
    return result
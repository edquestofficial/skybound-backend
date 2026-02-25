from core.role import Role
from database import execute_company_query, execute_insert_query
from core.config import db_query
from utility.pushnotify import send_notifications

def addTimeLine(comment, userinfo, docUrls):
    device_tokens = []
    inserted_id = execute_insert_query(db_query['COMPANY_TIMELINE']['INSERT'],comment,docUrls,userinfo['id'])
    
    query = db_query["USER"]["SELECT_ALL_DEVICE_TOKEN"]
    rows= execute_company_query(query)
    device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
   
    # send notification to all sales person
    if device_tokens:
        title = "Company timeline added"
        message = f"A Company timeline has been added."
        data = {
                "tabName": "Timeline",
                "id": str(inserted_id)
                }
        send_notifications(device_tokens, title, message, data)
    return True

def editTimeLine(timeline_id, comment, userinfo, docUrls):
    execute_company_query(db_query['COMPANY_TIMELINE']['UPDATE'],comment,docUrls,userinfo['id'], timeline_id)
    query = db_query["USER"]["SELECT_ALL_DEVICE_TOKEN"]
    rows= execute_company_query(query)
    device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
   
    # send notification to all sales person
    if device_tokens:
        title = "Company timeline updated"
        message = f"A Company timeline has been updated."
        data = {
                "tabName": "Timeline",
                "id": str(timeline_id)
                }
        send_notifications(device_tokens, title, message, data)
    return True  

def deleteTimeline(timeline_id, userinfo):
    execute_company_query(db_query['COMPANY_TIMELINE']['DELETE'],userinfo['id'] ,timeline_id)
   
    query = db_query["USER"]["SELECT_ALL_DEVICE_TOKEN"]
    rows= execute_company_query(query)
    device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
   
    # send notification to all sales person
    if device_tokens:
        title = "Company timeline deleted"
        message = f"A Company timeline has been deleted."
        send_notifications(device_tokens, title, message)
    return True 
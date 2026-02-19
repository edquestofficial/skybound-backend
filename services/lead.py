from database import execute_company_query, execute_filter_lead,fetch_single_record, update_query
from core.config import db_query
from schemas.lead import EditLead
from services.project import create_project
from utility.dateutility import ist_now
from core.role import Role

from utility.pushnotify import send_notify, send_notifications
from utility.statemgmt import state

# create the lead and find all salesperson to assign the lead and send notification  
def create_lead(lead,userinfo):
    try :
        #insert lead record
        id = 1
        if userinfo is not None:
            id = userinfo['id']
        else:
            state.setvalue('sb')  # Set a default value if userinfo is None
        result = execute_company_query(db_query['LEAD']['INSERT'],lead.name, lead.company_name,lead.city,lead.state,lead.contact_number,lead.enquiry_type,lead.email,lead.requirement,id)
        # get all sales person device token and send notification
        query = db_query["USER"]["SELECT_SALESPERSON_DEVICE_TOKEN"]
        rows= execute_company_query( query, Role.Sales.value, Role.SalesHead.value, Role.Admin.value)
        device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
        # send notification to all sales person
        if device_tokens:
            title = "New lead added"
            message = f"A new lead has been created."
            send_notifications(device_tokens, title, message)

        return True
    except Exception as e:
        print("Error in lead creation:", e)
        return None


def fetch_single(id):
    return execute_company_query(db_query['LEAD']['SELECT_BY_LEADID'],id)


def updateLead(id:int,item:EditLead, loggedin_userId:int):
    try :
        lead = fetch_single_record(db_query['LEAD']['SELECT_BY_LEADID'],id)
    
        if not lead:
           return False
        update_data = item.model_dump(exclude_unset=True,  by_alias=False)
        update_data['modify_date'] = ist_now()
        update_data['modify_by'] = loggedin_userId
        if update_data.get('assigned_to') not in (None, ""):
            update_data['assigned_by'] = loggedin_userId
            update_data['status']= 'inprogress'
            update_data['stage']= 'cold'
        update_data = {
            k: v for k, v in update_data.items()
            if v not in (None, "","0")
        }
        if item.stage and item.stage.lower() == "poraised":
            update_data['stage']= 'poraised'
        set_clause = ", ".join(f"{key}=?" for key in update_data.keys())
        values = list(update_data.values())
        values.append(id)

        query = db_query['LEAD']['UPDATE']
        result = update_query(query,set_clause, values)
         # get all sales person device token and send notification
        # if update_data.get('assigned_to') not in (None, ""):
        if item.assigned_to not in (None, ""):
            query = db_query["USER"]["SELECT_DEVICE_TOKEN_BY_USERID"]
            rows= execute_company_query( query, update_data.get('assigned_to'), Role.SalesHead.value, Role.Admin.value)
            device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
            query_user = db_query["USER"]["SELECT_USER_BYID"]
            user = execute_company_query(query_user, update_data.get('assigned_to'))
            # send notification to all sales person
            if device_tokens:
                title = "Lead assigned"
                message = f"A new lead({id}) has been assigned to {user[0]['name'] if user else 'Unknown User' }."
                send_notifications(device_tokens, title, message)
        if result and item.status and item.status.lower() == "closed":
            query = db_query["USER"]["SELECT_DEVICE_TOKEN_SALESHEAD_ADMIN"]
            rows= execute_company_query( query, Role.SalesHead.value, Role.Admin.value)
            device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
            # send notification to all sales person
            if device_tokens:
                title = "Lead closed"
                message = f"A lead has been closed. Lead ID: {id}"
                send_notifications(device_tokens, title, message)
        if result and item.stage and item.stage.lower() == "poraised":
            result  = create_project(id,loggedin_userId)
            query = db_query["USER"]["SELECT_SALESPERSON_DEVICE_TOKEN"]
            rows= execute_company_query( query, Role.Engineer.value, Role.EngineerHead.value, Role.Admin.value)
            device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
            # send notification to all sales person
            if device_tokens:
                title = "Project created"
                message = f"A new project has been created for Lead ID: {id}"
                send_notifications(device_tokens, title, message)
            return result
        
        else :
            return True
    except Exception as e:
        raise 


def count_lead(userinfo):
    if userinfo['role'] == Role.Admin.value or userinfo['role'] == Role.SalesHead.value:
        return execute_company_query(db_query['LEAD']['COUNT'])
    else :
         return execute_company_query(db_query['LEAD']['COUNT_BY_USER'],userinfo['id'])
    
def addTimeLine(leadId, comment, userinfo, docUrls):
    sales_device_tokens = []
    result = execute_company_query(db_query['LEAD_TIMELINE']['INSERT'],leadId,comment,docUrls,userinfo['id'])
    query = db_query["USER"]["SELECT_DEVICE_TOKEN_SALESHEAD_ADMIN"]
    rows= execute_company_query( query, Role.SalesHead.value, Role.Admin.value)
    device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
    if userinfo['role'] == Role.Admin.value or userinfo['role'] == Role.SalesHead.value:
        query = db_query["LEAD"]["SELECT_DEVICE_TOKEN_BY_LeadID"]
        rows= execute_company_query( query, leadId)
        sales_device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
    if len(sales_device_tokens) > 0:
        device_tokens.extend(sales_device_tokens)
    # send notification to all sales person
    if device_tokens:
        title = "Timeline updated"
        message = f"A timeline has been added to Lead ID: {leadId}"
        send_notifications(device_tokens, title, message)
    return result

def editTimeLine(timeline_id, comment, userinfo, docUrls):
    result = execute_company_query(db_query['LEAD_TIMELINE']['UPDATE'],comment,docUrls,userinfo['id'], timeline_id)
    return result

def deleteTimeline(timeline_id, userinfo):
    result = execute_company_query(db_query['LEAD_TIMELINE']['DELETE'], userinfo['id'], timeline_id)
    return result

LIKE_COLUMNS = {
    "city": "a.city",
    "state": "a.state",
    "enquiry_type": "a.enquiry_type",
}

EXACT_COLUMNS = {
    "id": "a.id",
    "status": "a.status",
    "assigned_to": "a.assigned_to",
}

def build_filters(filters):
    conditions = []
    values = []

    for key, column in LIKE_COLUMNS.items():
        value = filters.get(key)
        if value:
            value = value.strip()
            conditions.append(f"TRIM({column}) LIKE ?")
            values.append(f"%{value}%")

    for key, column in EXACT_COLUMNS.items():
        value = filters.get(key)
        if value is not None:
            conditions.append(f"{column} = ?")
            values.append(value)

    return conditions, values

def fetch_lead(lead,userinfo):
    user_id = userinfo['id']
    role = userinfo['role']
   
    query = db_query['LEAD']['SELECT_ALL']
    conditions = []
    values = []

     # 🔹 KEYSET PAGINATION
    if lead.last_id is not None:
        conditions.append(" a.id < ?")
        values.append(lead.last_id)
     # 🔹 FILTERS (whitelisted)
    filters = lead.model_dump(exclude_unset=True)
    filter_conditions, filter_values = build_filters(filters)
    conditions.extend(filter_conditions)
    values.extend(filter_values)    
     # 🔹 ROLE BASED CONDITION
    if Role.Sales.value == role and lead.id is None:
        conditions.append("(a.assigned_to IS NULL OR a.assigned_to = ?)")
        values.append(user_id)

    condition_str = " AND ".join(conditions)
    if len(conditions) > 0:
        condition_str = " AND " + condition_str
    values.append(lead.limit)
    result = execute_filter_lead(query,condition_str,values)
    if lead.id is not None:
        query = db_query['LEAD_TIMELINE']['SELECT']
        rows=execute_company_query(query,lead.id)
        for row in rows:
            urls = row.get("docs_urls", "")
            row["docs_urls"] = urls.split(",") if urls else []
        if len(result)>0:
             result[0]["timeline"] = rows
    return result
         
def to_sqlite_datetime(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)

def bulk_create_lead(data_rows,userinfo):
    try :
        for lead in data_rows:
            
            if lead:
                    execute_company_query(db_query['LEAD']['INSERT_BULK_LEAD'],lead['name'], lead['company name'],lead['city'],lead['state'],lead['contact 1'],lead['inquiry type'],lead['e mail'],lead['requirements'], lead['cold/hot/warm'],to_sqlite_datetime(lead['next follow up']),1,lead['open/closed'],None, to_sqlite_datetime(lead['date']))
        return True
    except Exception as e:
        print("Error in bulk lead creation:", e)
        return False     


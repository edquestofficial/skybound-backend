from database import execute_company_query, execute_filter_lead,fetch_single_record, update_query
from core.config import db_query
from schemas.lead import EditLead
from services.project import create_project
from datetime import datetime
from core.role import Role

from utility.pushnotify import send_notify, send_notifications
  

# create the lead and find all salesperson to assign the lead and send notification  
def create_lead(lead,userinfo):
    try :
        print("Lead Data:", lead, userinfo)
        #insert lead record
        result = execute_company_query(db_query['LEAD']['INSERT'],lead.name, lead.company_name,lead.city,lead.state,lead.contact_number,lead.enquiry_type,lead.email,lead.requirement,userinfo['id'])
        print("Lead created with ID:", result)
        # get all sales person device token and send notification
        query = db_query["USER"]["SELECT_SALESPERSON_DEVICE_TOKEN"]
        rows= execute_company_query( query, Role.Sales.value)
        device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
        # send notification to all sales person
        if device_tokens:
            title = "New Lead"
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
        update_data['modify_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_data['modify_by'] = loggedin_userId
        if update_data.get('assigned_to') not in (None, ""):
            update_data['assigned_by'] = loggedin_userId
            update_data['status']= 'inprogress'
            update_data['stage']= 'cold'
        update_data = {
            k: v for k, v in update_data.items()
            if v not in (None, "","0")
        }
        if item.stage == "poraised" :
            update_data['stage']= 'poraised'
        set_clause = ", ".join(f"{key}=?" for key in update_data.keys())
        values = list(update_data.values())
        values.append(id)

        query = db_query['LEAD']['UPDATE']
        result = update_query(query,set_clause, values)
        if result and  item.stage == "poraised":
           return create_project(id,loggedin_userId)
        else :
            return True
    except Exception as e:
        raise 


def count_lead(userinfo):
    if userinfo['role'] == Role.Admin.value:
        return execute_company_query(db_query['LEAD']['COUNT'])
    else :
         return execute_company_query(db_query['LEAD']['COUNT_BY_USER'],userinfo['id'])
    
def addTimeLine(leadId, comment, userinfo, docUrls):
    return execute_company_query(db_query['LEAD_TIMELINE']['INSERT'],leadId,comment,docUrls,userinfo['id'])


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
        conditions.append("AND a.id < ?")
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


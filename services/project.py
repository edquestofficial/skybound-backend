from core.role import Role
from database import execute_company_query,execute_filter_lead, fetch_single_record, update_query
from core.config import db_query
from schemas.project import UpdateModel
from utility.pushnotify import send_notify, send_notifications
from utility.dateutility import ist_now

def create_project(lead_id, user_id):
    execute_company_query(db_query['PROJECT']['INSERT'],lead_id, 'cold', 'open', 1, user_id)
    return True

def build_conditions(update_data: dict) -> str:
    a_keys = {"id", "assigned_to", "status"}
    c_keys = {"city", "state", "enquiry_type"}

    clauses = []

    clauses.extend( f"{'a' if k in a_keys else 'c'}.{k}=?"
    for k in update_data
    if k in a_keys or k in c_keys)

    return " AND ".join(clauses)


LIKE_COLUMNS = {
    "city": "c.city",
    "state": "c.state",
    "enquiry_type": "c.enquiry_type"
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




def fetch_project(proj,userinfo):
    user_id = userinfo['id']
    role = userinfo['role']
    query = db_query['PROJECT']['SELECT_ALL']
    conditions = []
    values = []
      # 🔹 KEYSET PAGINATION
    conditions.append("AND a.id > ?")
    values.append(proj.last_id)

    filters = proj.model_dump(exclude_unset=True)
    filter_conditions, filter_values = build_filters(filters)
    conditions.extend(filter_conditions)
    values.extend(filter_values)


     # 🔹 ROLE BASED CONDITION
    if Role.Engineer.value == role and proj.id is None:
        conditions.append("(a.assigned_to IS NULL OR a.assigned_to = ?)")
        values.append(user_id)
    condition_str = " AND ".join(conditions)
    values.append(proj.limit)
    result = execute_filter_lead(query,condition_str,values)
    if proj.id is not None:
        query = db_query['PROJECT_TIMELINE']['SELECT']
        rows=execute_company_query(query,proj.id)
        for row in rows:
            urls = row.get("docs_urls", "")
            row["docs_urls"] = urls.split(",") if urls else []
        result[0]['timeline']=rows
    return result

def count_project(userinfo):
    if userinfo['role'] == Role.Admin.value or userinfo['role'] == Role.EngineerHead.value:
        return execute_company_query(db_query['PROJECT']['COUNT'])
    else :
         return execute_company_query(db_query['PROJECT']['COUNT_BY_USER'],userinfo['id'])
    
def addTimeLine(projId, comment, userinfo, docUrls):
    result = execute_company_query(db_query['PROJECT_TIMELINE']['INSERT'],projId,comment,docUrls,userinfo['id'])
    query = db_query["USER"]["SELECT_DEVICE_TOKEN_SALESHEAD_ADMIN"]
    rows= execute_company_query( query, Role.EngineerHead.value, Role.Admin.value)
    device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
    # send notification to all sales person
    if device_tokens:
        title = "Project timeline Updated"
        message = f"A project timeline has been added for Project ID: {projId}"
        send_notifications(device_tokens, title, message)
    return result

def updateProject(id:int,item:UpdateModel, loggedin_userId:int):
    try :
        proj = fetch_single_record(db_query['PROJECT']['SELECT_BY_PROJID'],id)
    
        if not proj:
           return False
        update_data = item.model_dump(exclude_unset=True)
        update_data['modify_date'] = ist_now()
        update_data['modify_by'] = loggedin_userId
        if update_data.get('assigned_to') not in (None, ""):
            update_data['assigned_by'] = loggedin_userId
            update_data['status']= 'inprogress'

        update_data = {
            k: v for k, v in update_data.items()
            if v not in (None, "","0")
        }
       
        set_clause = ", ".join(f"{key}=?" for key in update_data.keys())
        values = list(update_data.values())
        values.append(id)

        query = db_query['PROJECT']['UPDATE']
        update_query(query,set_clause, values)
        # if update_data.get('assigned_to') not in (None, ""):
        if item.assigned_to not in (None, ""):
            query = db_query["USER"]["SELECT_DEVICE_TOKEN_BY_USERID"]
            rows= execute_company_query( query, update_data.get('assigned_to'), Role.EngineerHead.value, Role.Admin.value)
            device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
            # send notification to all sales person
            if device_tokens:
                title = "Project Assigned"
                message = f"A new project has been assigned. Project ID: {id}"
                send_notifications(device_tokens, title, message)
        # if update_data.get('stage') == "closed":
        if rows and item.status and item.status.lower() == "closed":
            query = db_query["USER"]["SELECT_DEVICE_TOKEN_SALESHEAD_ADMIN"]
            rows= execute_company_query( query, Role.EngineerHead.value, Role.Admin.value)
            device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
            # send notification to all sales person
            if device_tokens:
                title = "Project Closed"
                message = f"A project has been closed. Project ID: {id}"
                send_notifications(device_tokens, title, message)
        # if update_data.get('stage') == "poraised":
        if rows and  item.stage and item.stage.lower() == "reviewraised":    
            query = db_query["USER"]["SELECT_SALESPERSON_DEVICE_TOKEN"]
            rows= execute_company_query( query, Role.Engineer.value, Role.EngineerHead.value, Role.Admin.value)
            device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
            # send notification to all sales person
            if device_tokens:
                title = "Review Raised"
                message = f"Review Raised for Project ID: {id}"
                send_notifications(device_tokens, title, message)
           
        return True
        
    except Exception as e:
        raise 
from core.role import Role
from database import execute_company_query,execute_filter_lead, fetch_single_record, update_query, execute_project_query
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
    query = db_query['PROJECT']['SELECT_ALL_PROJECT']
    params = []
    if proj.id is not None:
        query += " AND p.id = ?"
        params.append(proj.id)

    if proj.city:
        query += " AND c.city = ?"
        params.append(proj.city)

    if proj.state:
        query += " AND c.state = ?"
        params.append(proj.state)

    if proj.enquiry_type:
        query += " AND c.enquiry_type = ?"
        params.append(proj.enquiry_type)

    if proj.status:
        query += " AND p.status = ?"
        params.append(proj.status)

    if proj.stage:
        query += " AND p.stage = ?"
        params.append(proj.stage)

    if proj.last_id:
        query += " AND p.id < ?"
        params.append(proj.last_id)
    
    if Role.Engineer.value == role and proj.id is None:
        query += """ AND 
        (
        p.id IN (
            SELECT project_id 
            FROM sb_project_user_mapping 
            WHERE user_id = ?
        )
        OR
        p.id NOT IN (
            SELECT project_id 
            FROM sb_project_user_mapping
        )
    )"""
        params.append(user_id)

    if Role.Admin.value == role or Role.EngineerHead.value == role:
        if proj.assigned_to:
            placeholders = ",".join(["?"] * len(proj.assigned_to))
            query += f"""
            AND p.id IN (
                SELECT project_id 
                FROM sb_project_user_mapping 
                WHERE user_id IN ({placeholders})
            )
            """
            assigned_users = [int(x) for x in proj.assigned_to]
            params.extend(assigned_users)
        
    
    query += " GROUP BY p.id ORDER BY p.id desc LIMIT ?"
    params.append(proj.limit)
    result = execute_project_query(query,params)
    
    if result and proj.id is not None:
        query = db_query['PROJECT_TIMELINE']['SELECT']
        rows=execute_company_query(query,proj.id)
        for row in rows:
            urls = row.get("docs_urls", "")
            row["docs_urls"] = urls.split(",") if urls else []
        result[0]['timeline']=rows
    return result


# def fetch_project(proj,userinfo):
#     user_id = userinfo['id']
#     role = userinfo['role']
#     query = db_query['PROJECT']['SELECT_ALL']
#     conditions = []
#     values = []
#       # 🔹 KEYSET PAGINATION
#     if proj.last_id is not None:
#         conditions.append("a.id < ?")
#         values.append(proj.last_id)

#     filters = proj.model_dump(exclude_unset=True)
#     filter_conditions, filter_values = build_filters(filters)
#     conditions.extend(filter_conditions)
#     values.extend(filter_values)


#      # 🔹 ROLE BASED CONDITION
#     if Role.Engineer.value == role and proj.id is None:
#         conditions.append("(a.assigned_to IS NULL OR a.assigned_to = ?)")
#         values.append(user_id)
#     condition_str = " AND ".join(conditions)
    
#     if len(conditions) > 0:
#         condition_str = " AND " + condition_str
#     values.append(proj.limit)
#     result = execute_filter_lead(query,condition_str,values)
#     if proj.id is not None:
#         query = db_query['PROJECT_TIMELINE']['SELECT']
#         rows=execute_company_query(query,proj.id)
#         for row in rows:
#             urls = row.get("docs_urls", "")
#             row["docs_urls"] = urls.split(",") if urls else []
#         result[0]['timeline']=rows
#     return result

def count_project(userinfo):
    if userinfo['role'] == Role.Admin.value or userinfo['role'] == Role.EngineerHead.value:
        return execute_company_query(db_query['PROJECT']['COUNT'])
    else :
         return execute_company_query(db_query['PROJECT']['COUNT_BY_USER'],userinfo['id'])
    
def addTimeLine(projId, comment, userinfo, docUrls):
    sales_device_tokens = []
    result = execute_company_query(db_query['PROJECT_TIMELINE']['INSERT'],projId,comment,docUrls,userinfo['id'])
    query = db_query["USER"]["SELECT_DEVICE_TOKEN_SALESHEAD_ADMIN"]
    rows= execute_company_query( query, Role.EngineerHead.value, Role.Admin.value)
    device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
    if userinfo['role'] == Role.Admin.value or userinfo['role'] == Role.EngineerHead.value:
        query = db_query["PROJECT"]["SELECT_DEVICE_TOKEN_BY_PROJID"]
        rows= execute_company_query( query, projId)
        sales_device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
    if len(sales_device_tokens) > 0:
        device_tokens.extend(sales_device_tokens)
    # send notification to all sales person
    if device_tokens:
        title = "Project timeline updated"
        message = f"A project timeline has been added for Project ID: {projId}"
        send_notifications(device_tokens, title, message)
    return result

def updateProject(id:int,item:UpdateModel, loggedin_userId:int):
    try :
        proj = fetch_single_record(db_query['PROJECT']['SELECT_BY_PROJID'],id)
    
        if not proj:
           return False
        # if update_data.get('assigned_to') not in (None, ""):
        if len(item.assigned_to) > 0:
            assign_project_user(id, item.assigned_to)
            query = db_query["USER"]["SELECT_DEVICE_TOKEN_BY_USERIDs"]
            query = query.replace("#", ",".join(str(user_id) for user_id in item.assigned_to))
            rows= execute_company_query( query, Role.EngineerHead.value, Role.Admin.value)
            device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
            query_user = db_query["USER"]["SELECT_USER_BYID_PROJECT"]
            query_user = query_user.replace("placeholder", ",".join(str(user_id) for user_id in item.assigned_to))
            user = execute_company_query(query_user)
            user_name = ",".join(str(row['name']) for row in user)
            # send notification to all sales person
            if device_tokens:
                title = "Project assigned"
                message = f"A new project({id}) has been assigned to {user_name}."
                send_notifications(device_tokens, title, message)
        update_data = item.model_dump(exclude_unset=True)
        update_data['modify_date'] = ist_now()
        update_data['modify_by'] = loggedin_userId
        if len(item.assigned_to) > 0 :
            update_data['assigned_by'] = loggedin_userId
            update_data['status'] = 'inprogress'

        update_data = {
            k: v for k, v in update_data.items()
            if v not in (None, "", "0") and not isinstance(v, list)
        }
       
        set_clause = ", ".join(f"{key}=?" for key in update_data.keys())
        values = list(update_data.values())
        values.append(id)

        query = db_query['PROJECT']['UPDATE']
        update_query(query,set_clause, values)
        
        # if update_data.get('stage') == "closed":
        if item.status and item.status.lower() == "closed":
            query = db_query["USER"]["SELECT_DEVICE_TOKEN_SALESHEAD_ADMIN"]
            rows= execute_company_query( query, Role.EngineerHead.value, Role.Admin.value)
            device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
            # send notification to all sales person
            if device_tokens:
                title = "Project closed"
                message = f"A project has been closed. Project ID: {id}"
                send_notifications(device_tokens, title, message)
        # if update_data.get('stage') == "poraised":
        if item.status and item.status.lower() == "raise-review":    
            query = db_query["USER"]["SELECT_SALESPERSON_DEVICE_TOKEN"]
            rows= execute_company_query( query, Role.Engineer.value, Role.EngineerHead.value, Role.Admin.value)
            device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
            # send notification to all sales person
            if device_tokens:
                title = "Review raised"
                message = f"Review raised for Project ID: {id}"
                send_notifications(device_tokens, title, message)
           
        return True
        
    except Exception as e:
        print("Exception in updateProject", e)
        raise 

# this function is used to assign a project to multiple users, it will take project id and list of user id , first delete alll mapping on the basis of proj id then assign the project to those users by inserting records in project_user_mapping table 
def assign_project_user(projid, user_ids):
    try:
        if len(user_ids) == 0:
            return
        execute_company_query(db_query['PROJECT']['DELETE_PROJECT_USER_MAPPING'], projid)
        for user_id in user_ids:
            execute_company_query(db_query['PROJECT']['INSERT_PROJECT_USER_MAPPING'], projid, user_id)
        return True
    except Exception as e:
        print("Exception in assign_project_user", e)
        return False
    
def editTimeLine(timeline_id,comment, userinfo, docUrls):
    result = execute_company_query(db_query['PROJECT_TIMELINE']['UPDATE'],comment,docUrls,userinfo['id'], timeline_id)
    query = db_query["USER"]["SELECT_DEVICE_TOKEN_SALESHEAD_ADMIN"]
    rows= execute_company_query( query, Role.EngineerHead.value, Role.Admin.value)
    device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
    # send notification to all sales person
    if device_tokens:
        title = "Project timeline updated"
        message = f"A timeline has been updated"
        send_notifications(device_tokens, title, message)
    
    return result
def deleteTimeline(timeline_id, userinfo):
    result = execute_company_query(db_query['PROJECT_TIMELINE']['DELETE'], userinfo['id'], timeline_id)
    query = db_query["USER"]["SELECT_DEVICE_TOKEN_SALESHEAD_ADMIN"]
    rows= execute_company_query( query, Role.EngineerHead.value, Role.Admin.value)
    device_tokens = [row['device_id'] for row in rows if row.get('device_id')]
    # send notification to all sales person
    if device_tokens:
        title = "Project timeline deleted"
        message = f"A timeline has been deleted"
        send_notifications(device_tokens, title, message)
    return True
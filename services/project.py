from datetime import date
from core.role import Role
from database import execute_company_query,execute_select_query, fetch_single_record, update_query
from core.config import db_query
from schemas.project import SearchProject

def create_project(lead_id, user_id):
    execute_company_query(db_query['PROJECT']['INSERT'],lead_id, 'cold', 'open', 1, user_id)
    return True

def fetch_project(proj,userinfo):
    user_id = userinfo['id']
    role = userinfo['role']
    query = db_query['PROJECT']['SELECT']
    conditions = ""
    values = []
    update_data = proj.model_dump(exclude_unset=True)
    update_data = {
        k: v for k, v in update_data.items()
        if v not in (None, "","0")
    }
    if len(update_data)>0 :
        conditions = " AND ".join(f"{key}=?" for key in update_data.keys())
        values = list(update_data.values())
    if Role.Engineer.value == role :
        if conditions != "" :
            conditions += " AND "

        conditions += " (assigned_to is NULL) OR assigned_to = ? "
        values.append(user_id)

    result = execute_select_query(query,conditions,values)
    if proj.id is not None:
        query = db_query['PROJECT_TIMELINE']['SELECT']
        rows=execute_company_query(query,proj.id)
        for row in rows:
            urls = row.get("docs_urls", "")
            row["docs_urls"] = urls.split(",") if urls else []
        result[0]['timeline']=rows
    return result

def count_project(userinfo):
    if userinfo['role'] == Role.Admin.value:
        return execute_company_query(db_query['PROJECT']['COUNT'])
    else :
         return execute_company_query(db_query['PROJECT']['COUNT_BY_USER'],userinfo['id'])
    
def addTimeLine(projId, comment, userinfo, docUrls):
    return execute_company_query(db_query['PROJECT_TIMELINE']['INSERT'],projId,comment,docUrls,userinfo['id'])

def updateProject(id:int,item:SearchProject, loggedin_userId:int):
    try :
        proj = fetch_single_record(db_query['PROJECT']['SELECT_BY_PROJID'],id)
    
        if not proj:
           return False
        update_data = item.model_dump(exclude_unset=True)
        update_data['modify_date'] = date.today()
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
        return True
        
    except Exception as e:
        raise 
from database import execute_company_query, execute_select_query,fetch_single_record, update_query
from core.config import db_query
from schemas.lead import EditLead
from services.project import create_project
from datetime import date
from core.role import Role
  
def create_lead(lead,userinfo):
    return execute_company_query(db_query['LEAD']['INSERT'],lead.name, lead.company_name,lead.city,lead.state,lead.contact_number,lead.enquiry_type,lead.email,lead.requirement,userinfo['id'])

def fetch_single(id):
    return execute_company_query(db_query['LEAD']['SELECT_BY_LEADID'],id)


def updateLead(id:int,item:EditLead, loggedin_userId:int):
    try :
        lead = fetch_single_record(db_query['LEAD']['SELECT_BY_LEADID'],id)
    
        if not lead:
           return False
        update_data = item.model_dump(exclude_unset=True)
        update_data['modify_date'] = date.today()
        update_data['modify_by'] = loggedin_userId
        if update_data.get('assigned_to') not in (None, ""):
            update_data['assigned_by'] = loggedin_userId
            update_data['status']= 'inprogress'
            update_data['stage']= 'cold'
        update_data = {
            k: v for k, v in update_data.items()
            if v not in (None, "","0")
        }
        if item.stage == "poraised" and item.close:
             update_data['status']= 'closed'
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
    print("docs urls", docUrls)
    return execute_company_query(db_query['LEAD_TIMELINE']['INSERT'],leadId,comment,docUrls,userinfo['id'])

def fetch_lead(lead,userinfo):
    user_id = userinfo['id']
    role = userinfo['role']
    query = db_query['LEAD']['SELECT_ALL']
    conditions = ""
    values = []
    update_data = lead.model_dump(exclude_unset=True)
    update_data = {
        k: v for k, v in update_data.items()
        if v not in (None, "","0")
    }
    if len(update_data)>0 :
        conditions = " AND ".join(f"a.{key}=?" for key in update_data.keys())
        values = list(update_data.values())
    if Role.Sales.value == role :
        if conditions != "" :
            conditions += " AND "

        conditions += " (a.assigned_to is NULL) OR a.assigned_to = ? "
        values.append(user_id)

    result = execute_select_query(query,conditions,values)
    if lead.id is not None:
        query = db_query['LEAD_TIMELINE']['SELECT']
        rows=execute_company_query(query,lead.id)
        for row in rows:
            urls = row.get("docs_urls", "")
            row["docs_urls"] = urls.split(",") if urls else []

        result[0]["timeline"] = rows
    return result
         



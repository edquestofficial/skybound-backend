from core.role import Role
from database import execute_company_query
from core.config import db_query

def create_project(lead_id, user_id):
    execute_company_query(db_query['PROJECT']['INSERT'],lead_id, 'cold', 'open', 1, user_id)
    return True

def fetch_project(userId,projid,userinfo):
    role = int(userinfo['role'])
    id = int(userinfo['id'])
    if role == Role.Admin.value:
        if userId != "" and projid == "" :
          result =  execute_company_query(db_query['PROJECT']['SELECT_BY_USER'],int(userId))
        elif projid !="":
            result =  execute_company_query(db_query['PROJECT']['SELECT_BY_PROJID'],int(projid))
        elif userId == "" and projid == "" :
             result =  execute_company_query(db_query['PROJECT']['SELECT'])
    elif role == Role.Sales.value:
        if projid !="":
            result =  execute_company_query(db_query['PROJECT']['SELECT_BY_PROJID_ASSIGN'],int(projid),id)
        else:
            result =  execute_company_query(db_query['PROJECT']['UNASSIGN_ASSIGN_PROJ'],id)

    return result
   
def count_project(userinfo):
    if userinfo['role'] == Role.Admin.value:
        return execute_company_query(db_query['PROJECT']['COUNT'])
    else :
         return execute_company_query(db_query['PROJECT']['COUNT_BY_USER'],userinfo['id'])
    
def addTimeLine(projId, comment, userinfo, docUrls):
    return execute_company_query(db_query['PROJECT_TIMELINE']['INSERT'],projId,comment,docUrls,userinfo[id])
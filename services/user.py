from core.role import Role
from database import execute_company_query, execute_query,fetch_single_record
from core.config import Settings, db_query

def fetch_user(userId, role, userinfo):
    logged_role = userinfo['role']
    id = userinfo['id']
    if logged_role == Role.Admin.value:
        if userId == "" and role != "":
            users = execute_company_query(db_query['USER']['SELECT_USER_BY_ROLE'],role)
            
        elif userId != "" and role=="":
            users = execute_company_query(db_query['USER']['SELECT_USER_BYID'],userId)
            
        elif userId =="" and role == "":
            users = execute_company_query(db_query['USER']['SELECT_USER'])
       
        return users
    elif id:
        users = execute_company_query(db_query['USER']['SELECT_USER_BYID'],id)
        return users
    else :
        return []
       
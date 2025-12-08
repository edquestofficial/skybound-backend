from core.role import Role
from database import execute_company_query,fetch_single_record,update_query
from core.config import db_query
from datetime import date

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
       
def EditUser(id,EditUser,loggedin_userId):
    try :
        user = fetch_single_record(db_query['USER']['SELECT_USER_BYID'],id)
    
        if not user:
           return False
        update_data = EditUser.model_dump(exclude_unset=True)
        update_data['modify_date'] = date.today()
        update_data['modify_by'] = loggedin_userId
        update_data = {
            k: v for k, v in update_data.items()
            if v not in (None, "","0")
        }
        
        set_clause = ", ".join(f"{key}=?" for key in update_data.keys())
        values = list(update_data.values())
        values.append(id)
        query = db_query['USER']['UPDATE']
        result = update_query(query,set_clause, values)
        return True
    except Exception as e:
        raise 
from core.role import Role
from database import execute_company_query, execute_select_query,fetch_single_record,update_query
from core.config import db_query
from datetime import datetime

# def fetch_user(userId, role, userinfo):
#     logged_role = userinfo['role']
#     id = userinfo['id']
#     users = None
#     if logged_role == Role.Admin.value:
#       if userId is None and role is not None:
#         users = execute_company_query(db_query['USER']['SELECT_USER_BY_ROLE'], role)

#     elif userId is not None and role is None:
#         users = execute_company_query(db_query['USER']['SELECT_USER_BYID'], userId)

#     elif userId is None and role is None:
#         users = execute_company_query(db_query['USER']['SELECT_USER'])
       
#         return users
#     elif id:
#         users = execute_company_query(db_query['USER']['SELECT_USER_BYID'],id)
#         return users
#     else :
#         return []
       
def EditUser(id,EditUser,loggedin_userId):
    try :
        user = fetch_single_record(db_query['USER']['SELECT_USER_BYID'],id)
    
        if not user:
           return False
        update_data = EditUser.model_dump(exclude_unset=True)
        update_data['modify_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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


def fetchUser(user, userinfo):
    user_id = userinfo['id']
    role = userinfo['role']
    query = db_query['USER']['SELECT_ALL']
    conditions = ""
    values = []
    update_data = user.model_dump(exclude_unset=True)
    update_data = {
        k: v for k, v in update_data.items()
        if v not in (None, "","0")
    }
    if len(update_data)>0 :
        conditions = " AND ".join(f"{key}=?" for key in update_data.keys())
        values = list(update_data.values())
    if Role.Admin.value == role:
        return execute_select_query(query,conditions,values)
    else :
         return execute_company_query(db_query['USER']['SELECT_USER_BYID'],user_id)
    

def reset_password(emailid):
   query = db_query['USER']['SELECT_USER_BYEMAILID']
   return execute_company_query(query,emailid)

def change_password(oldpwd,newpwd):
     
     user = fetch_single_record(db_query['USER']['SELECT_USER_BYID'],id)
    
   
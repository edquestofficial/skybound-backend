from core.role import Role
from database import execute_company_query, execute_query,fetch_single_record, update_record
from core.config import db_query
from schemas.lead import EditLead
from services.project import create_Project

  
def fetch_single(id):
    return execute_company_query(db_query['LEAD']['SELECT_BY_LEADID'],id)
def updateLead(id:int,item:EditLead):
    try :
        lead = fetch_single_record(db_query['LEAD']['SELECT_BY_LEADID'],id)
    
        if not lead:
           return False
        update_data = item.model_dump(exclude_unset=True)
        update_data = {
            k: v for k, v in update_data.items()
            if v not in (None, "","0")
        }

        set_clause = ", ".join(f"{key}=?" for key in update_data.keys())
        values = list(update_data.values())
        values.append(id)

        result = update_record(set_clause, values)
        if result and  item.status == "poraised":
           return create_Project()
        else :
            return True
    except Exception as e:
        raise 

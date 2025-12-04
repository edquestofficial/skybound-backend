from fastapi import APIRouter, HTTPException,Depends
from schemas.company import Company
from database import execute_query, execute_company_query

from models.response import response
from core.role import Role
from core.config import db_query
from utility.statemgmt import state

router = APIRouter()

@router.post("/register")
def register(company: Company):
    if(company.name and company.comany_code):
        try :
            # Check existing user
            cur = execute_query(db_query['COMPANY']['SELECT_COMPANY_NAME'], company.name)
            if cur:
                raise HTTPException(400, "Company already exists")

            execute_query(db_query['COMPANY']['INSERT'],company.name, company.comany_code,company.active)
            state.setvalue(company.comany_code)

            execute_company_query(db_query['USER']['CREATE'])
            execute_company_query(db_query['LEAD']['CREATE'])
            execute_company_query(db_query['PROJECT']['CREATE'])
            execute_company_query(db_query['LEAD_TIMELINE']['CREATE'])
            execute_company_query(db_query['PROJECT_TIMELINE']['CREATE'])
            
            return response(
                    status="success",
                    code=200,
                    message="Company registered successfully and DB created successfully",
                    data=[]
                )
        except Exception as e:
            print("exception in company registraion", e)
            raise HTTPException(400, e)
    else:
         raise HTTPException(400, "Company Name and Alias name is compulsury.")

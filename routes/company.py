from fastapi import APIRouter, HTTPException,Depends
from schemas.company import Company
from database import execute_query, init_db,execute_company_query, truncate_table

from models.response import Response
from core.role import Role
from core.config import db_query
from utility.statemgmt import state
import os

router = APIRouter()

@router.post("/register")
def register(company: Company):
    if(company.name and company.comany_code):
        try :
            # Check existing user
            cur = execute_query(db_query['COMPANY']['SELECT_COMPANY_NAME'], company.name)
            if cur:
                raise HTTPException(400, "Company already exists")

            execute_query(db_query['COMPANY']['INSERT'],company.name, company.comany_code,1)
            state.setvalue(company.comany_code)

            execute_company_query(db_query['USER']['CREATE'])
            execute_company_query(db_query['LEAD']['CREATE'])
            execute_company_query(db_query['PROJECT']['CREATE'])
            execute_company_query(db_query['LEAD_TIMELINE']['CREATE'])
            execute_company_query(db_query['PROJECT_TIMELINE']['CREATE'])
            execute_company_query(db_query['NOTIFICATION']['CREATE'])
            
            return Response(
                    status=True,
                    code=200,
                    message="Company registered successfully and DB created successfully",
                    data=[]
                )
        except Exception as e:
           return Response(
                    status=False,
                    code=400,
                    message= str(e),
                    data=[]

                )
    else:
        return Response(
                status=False,
                code=400,
                message="Company name and alias name is compulsory",
                data=[]
            )
    
@router.get("/setupdb")
def setup_db():
    try :
        # os.remove("skybound.db")
        # query = db_query['COMPANY']['CREATE']+ db_query['STATE']['CREATE']+db_query['STATE']['INSERT']
        # init_db(query)
        truncate_table('<>_notification')
        
        return Response(
                status=True,
                code=200,
                message="DB created successfully",
                data=[]
            )
    except Exception as e:
       return Response(
                status=False,
                code=400,
                message="Something went wrong !!+ error:"+ str(e),
                data=[]
            )

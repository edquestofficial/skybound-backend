import shutil
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException,Depends, UploadFile
from schemas.company import Company
from database import execute_query, init_db,execute_company_query, truncate_table, create_table

from models.response import Response
from core.role import Role
from core.config import db_query
from services.company import addTimeLine, editTimeLine
from utility.auth import role_required
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
        # query = db_query['COMPANY']['CREATE']+ db_query['STATE']['CREATE']+db_query['STATE']['INSERT']+db_query['COMPANY_TIMELINE']['CREATE']
        # init_db(query)
        # truncate_table('<>_notification')
        # 
        query = db_query['LEAD_TIMELINE']['DELETE_TABLE']+db_query['LEAD_TIMELINE']['CREATE'] +db_query['PROJECT_TIMELINE']['DELETE_TABLE']+db_query['PROJECT_TIMELINE']['CREATE']+db_query['COMPANY_TIMELINE']['DELETE_TABLE']+db_query['COMPANY_TIMELINE']['CREATE']+ db_query['PROJECT']['CREATE_PROJECT_USER_MAPPING']   
        create_table(query)
        
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

@router.get("/gettimeline")
def get_timeline( userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead, Role.Sales, Role.SalesHead, Role.HR, Role.Customer]))):
    try:
        timeline = execute_company_query(db_query['COMPANY_TIMELINE']['SELECT'])
        for row in timeline:
            urls = row.get("docs_urls", "")
            row["docs_urls"] = urls.split(",") if urls else []
        return Response(
                status=True,
                code=200,
                message="Timeline fetched successfully",
                data=timeline
            )
    except Exception as e:
       return Response(
                status=False,
                code=400,
                message="Something went wrong !!+ error:"+ str(e),
                data=[]
            )

@router.post("/timeline")
def create_timeline( comment: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead, Role.Sales, Role.SalesHead, Role.HR, Role.Customer]))):
    saved_files = []
    docs :str = ""
    if files:
        upload_dir = "Company_Doc"
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            file_location = f"{upload_dir}/{file.filename}"
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file_location)
        docs = ",".join(saved_files)
    
    if files  or comment :
        addTimeLine(comment, userinfo, docs)
    return Response(
            status=True,
            code=200,
            message="Comment added successfully",
            data=[]
        )

@router.post("/timelineEdit")
def edit_timeline(id: int = Form(...), docs_urls :Optional[str] = Form(None),comment: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead, Role.Sales, Role.SalesHead, Role.HR, Role.Customer]))):
    saved_files = []
   
    if files:
        upload_dir = "Company_Doc"
        os.makedirs(upload_dir, exist_ok=True)
        if docs_urls and docs_urls[-1] != ",":
            docs_urls += ","
        else:            
            docs_urls = ""
        for file in files:
            file_location = f"{upload_dir}/{file.filename}"
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file_location)
        docs_urls += ",".join(saved_files)
    
    if files  or comment :
        editTimeLine(id, comment, userinfo, docs_urls)
    return Response(
            status=True,
            code=200,
            message="Timeline edited successfully",
            data=[]
        )
@router.get("/timelineDelete")
def delete_timeline(id: int, userinfo = Depends(role_required([Role.Admin, Role.Engineer, Role.EngineerHead, Role.Sales, Role.SalesHead, Role.HR, Role.Customer]))):
    execute_company_query(db_query['COMPANY_TIMELINE']['DELETE'],userinfo['id'] ,id)
    return Response(
            status=True,
            code=200,
            message="Timeline deleted successfully",
            data=[]
        )
   
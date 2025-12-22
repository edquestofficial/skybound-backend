import io
import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException,Depends, UploadFile
from schemas.lead import Lead, EditLead, SearchLead
import pandas as pd
import numpy as np
from models.response import Response
from core.role import Role
from utility.auth import role_required
from services.lead import bulk_create_lead, create_lead, updateLead, count_lead, fetch_lead, addTimeLine

lead_router = APIRouter()


@lead_router.post("/create")
def create(lead: Lead,userinfo = Depends(role_required([Role.Admin]))):
    response  = create_lead(lead,userinfo)
    if response is not None:
        return Response(
                status=True,
                code=200,
                message="Lead created successfully",
                data=[]
            )
    else:
         return Response(
                status=False,
                code=200,
                message="Invalid data",
                data=[]
            )


@lead_router.post("/")
def fetch( lead :SearchLead, userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
   
    result = fetch_lead(lead,userinfo)
    return Response(
            status=True,
            code=200,
            message="Lead fetch successfully",
            data=result
        )

@lead_router.post("/edit")
def edit(update:EditLead, userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    
    if len(update.id) == 0:
        return Response(
            status=False,
            code=400,
            message="please provide the atleast one lead id",
            data=[]
        )
    else:
        ids = update.id
        del update.id
        for id in ids:
            loggedin_userId = userinfo['id']
            updateLead(id,update, loggedin_userId)
    return Response(
            status=True,
            code=200,
            message="Lead update successfully",
            data=[]
                )   
   
@lead_router.get("/count")
def dashboardCount( userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    result = count_lead(userinfo)
    return Response(
            status=True,
            code=200,
            message="Fetch Count successfully",
            data=result
        )

@lead_router.post("/timeline")
def create( id: int = Form(...),
    comment: str = Form(...),
    files: List[UploadFile] = File(None),userinfo = Depends(role_required([Role.Admin, Role.Sales]))):
    saved_files = []
    docs :str = ""
    if files:
        upload_dir = "Lead_Doc"
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            file_location = f"{upload_dir}/{id}_{file.filename}"
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file_location)
            docs = ",".join(saved_files)
    addTimeLine(id, comment, userinfo, docs)
    return Response(
            status=True,
            code=200,
            message="Comment added successfully",
            data=[]
        )

EXPECTED_HEADERS = [
    "s no.", "date", "name", "company name", "city", "state", "contact 1",
    "inquiry type", "e mail", "requirements", "status", "skybound person",
    "cold/hot/warm", "open/closed", "next follow up"
]
@lead_router.post("/bulkupload")
async def bulk_upload(file: UploadFile = File(...),userinfo = Depends(role_required([Role.Admin]))):
    try:
        # Read the file's content into memory
        contents = await file.read()
        buffer = io.BytesIO(contents)
        df = pd.read_excel(buffer)

        # --- 1. Header Validation ---
        header_map = {col: str(col).strip().lower() for col in df.columns}
        
        # Get a set of the standardized headers from the file
        standardized_file_headers = set(header_map.values())
        required_set = set(EXPECTED_HEADERS)

        # Check if all required headers are present in the file
        if not required_set.issubset(standardized_file_headers):
            missing_headers = list(required_set - standardized_file_headers)
            return Response(
                status=False,
                code=400,
                message="Invalid file format. Missing required headers.",
                error=missing_headers
            )
# --- 2. Data Processing (ALL FIXES APPLIED) ---        
        # Rename the DataFrame columns to your standardized lowercase names
        df = df.rename(columns=header_map)
        
        # --- FIX 1: Handle NaN, empty strings, and single spaces ---
        # This replaces all of them with None, which becomes NULL in MySQL
        df = df.replace({np.nan: None, '': None, ' ': None})
        
        # --- FIX 2: Handle bad DATE columns ---
        # 'errors=coerce' turns any bad date (like 'pending') into 'NaT'
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['next follow up'] = pd.to_datetime(df['next follow up'], errors='coerce')
        
        # --- FIX 3: Handle bad NUMBER columns ---
        # This fixes errors like "Incorrect integer value: ' ' for column 's no.'"
        # It turns any bad number (like 'N/A' or text) into 'NaN' (Not a Number)
        df['s no.'] = pd.to_numeric(df['s no.'], errors='coerce')
        
        # --- FIX 4: Convert all 'NaT' and 'NaN' into None ---
        
        df = df.replace({pd.NaT: None, np.nan: None})        
        # Convert the DataFrame to a list of dictionaries
        data_rows = df.to_dict(orient="records")
        bulk_create_lead(data_rows, userinfo)
    except Exception as e:
        return Response(
            status=False,
            code=500,
            message="An error occurred while processing the file.",
            error=str(e)
        )




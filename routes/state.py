from fastapi import APIRouter, HTTPException,Depends
from schemas.company import Company
from database import execute_query, execute_company_query

from models.response import Response
from core.role import Role
from core.config import db_query
from schemas.state import State
from utility.auth import role_required
from utility.statemgmt import state
from services.state import fetch_cities, getStateInfo, getCityByState, getStates, fetch_cities



state_router = APIRouter()

# @state_router.post("/")
# async def registerCity(state: State, userinfo = Depends(role_required([Role.Admin]))):
#     data =  getStates()
#     for item in data:
#         if item['name'] == state.name:
#             result = await fetch_cities(state.name)
#     if result:
#         return Response(
#                 status=True,
#                 code=200,
#                 message="City registered successfully",
#                 data=result
#             )
#     else:
#          return Response(
#                 status=False,
#                 code=200,
#                 message="Invalid data",
#                 data=[]
#             )
    
@state_router.get("/")
def getState(userinfo = Depends(role_required([Role.Admin, Role.Sales, Role.SalesHead, Role.Engineer, Role.EngineerHead,Role.HR]))):
    try :
            result = getStateInfo()
            if result:
                return Response(
                        status=True,
                        code=200,
                        message="State fetch successfully",
                        data=result
                    )
            else:
                return Response(
                        status=False,
                        code=200,
                        message="Invalid data",
                        data=[]
                    )
    except Exception as e:
         return Response(
                status=False,
                code=500,
                message=str(e),
                data=[]
            )
    
@state_router.get("/{statename}")
async def getCity(statename: str, userinfo = Depends(role_required([Role.Admin, Role.Sales, Role.SalesHead, Role.Engineer, Role.EngineerHead,Role.HR]))):
    result = await fetch_cities(statename)
    if result:  
        return Response(
                status=True,
                code=200,
                message="City fetch successfully",
                data=result
            )
    else:
         return Response(
                status=False,
                code=200,
                message="Invalid data",
                data=[]
            )

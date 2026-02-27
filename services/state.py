from database import excute_simple_query, get_state
from core.config import db_query
from fastapi import FastAPI, HTTPException
import httpx
  
async def fetch_cities(state: str):
     async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
        try:
            r = await client.post(
                "https://countriesnow.space/api/v0.1/countries/state/cities",
                json={"country": 'India', "state": state}
            )
            cities = r.json()["data"]
            r.raise_for_status()
            cleaned_cities = [city.replace("ā", "a") for city in cities]

            return cleaned_cities
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=str(e))
    # return excute_simple_query(db_query['CITY']['INSERT'],state.stateid, state.cityname)

def getStateInfo():
    return get_state(db_query['STATE']['SELECT_ALL'])

def getCityByState(stateid:int):
    return excute_simple_query(db_query['CITY']['SELECT_BY_STATEID'],stateid)

def getStates():
    return excute_simple_query(db_query['STATE']['SELECT_ALL'])
from fastapi import FastAPI,Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from models.response import Response
import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware
from routes.user import router as user_router
from routes.company import router as company_router
from routes.lead import lead_router
from routes.project import project_router

app = FastAPI(title="Skybound App", swagger_ui_parameters={"persistAuthorization": True} )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    # Detect extra field error
    for error in exc.errors():
        if error.get("type") == "extra_forbidden":
            field_name = error.get("loc")[-1]
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Extra field '{field_name}' is not allowed."
                }
            )
        else:
            return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid payload data"
            }
    )
    
    

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def log_request(request, call_next):
    response = await call_next(request)
    return response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


logger = logging.getLogger(__name__)
app.include_router(user_router, prefix="/user")

app.include_router(lead_router, prefix="/lead")
app.include_router(project_router, prefix="/project")
app.include_router(company_router, prefix="/company")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)
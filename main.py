from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware
from routes.user import router as user_router
from routes.company import router as company_router
from routes.lead import lead_router
from routes.project import project_router
from routes.state import state_router

app = FastAPI(title="Skybound App", swagger_ui_parameters={"persistAuthorization": True} )

app.mount("/Lead_Doc", StaticFiles(directory="Lead_Doc"), name="images")
app.mount("/Project_Doc", StaticFiles(directory="Project_Doc"), name="images")
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_list =[]
    # Detect extra field error
    for error in exc.errors():
        field_name = error.get("loc")[-1]
        error_list.append({field_name:error.get("msg")})
                    
    return JSONResponse(status_code=400, content=error_list)
    
    

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
app.include_router(state_router, prefix="/state")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)
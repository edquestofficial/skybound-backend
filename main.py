from fastapi import FastAPI,Request
import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware
from routes.user import router as user_router
from routes.company import router as company_router
from routes.lead import lead_router

app = FastAPI(title="Skybound App", swagger_ui_parameters={"persistAuthorization": True} )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def log_request(request, call_next):
    print("Request received")
    response = await call_next(request)
    return response
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


logger = logging.getLogger(__name__)
app.include_router(user_router, prefix="/user")
app.include_router(company_router, prefix="/company")
app.include_router(lead_router, prefix="/lead")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)
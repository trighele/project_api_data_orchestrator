from fastapi import FastAPI
from project_api_data_orchestrator.api import jobs

app = FastAPI(title="Data Orchestrator API")

app.include_router(jobs.router, prefix="/jobs")

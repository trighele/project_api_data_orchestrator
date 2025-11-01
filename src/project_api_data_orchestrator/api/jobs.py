from fastapi import APIRouter, BackgroundTasks
from project_api_data_orchestrator.jobs.fantasy_football import update_players_depthchart
from project_api_data_orchestrator.utils.job_runner import create_job_record, run_job_in_background
from project_api_data_orchestrator.db.connection import get_connection

router = APIRouter()

@router.post("/fantasy_football/update_players_data")
def update_team(background_tasks: BackgroundTasks):
    job_id = create_job_record("update_players_data")
    background_tasks.add_task(run_job_in_background, job_id, update_players_depthchart)
    return {"job_id": job_id, "status": "queued"}

@router.get("/status/{job_id}")
def get_job_status(job_id: int):
    conn = get_connection(DB_NAME='job_data')
    cursor = conn.cursor()
    cursor.execute("SELECT id, job_name, status, started_at, completed_at, message FROM orchestrator_jobs WHERE id=%s;", (job_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return {"error": "Job not found"}
    return {
        "id": row[0],
        "job_name": row[1],
        "status": row[2],
        "started_at": row[3],
        "completed_at": row[4],
        "message": row[5],
    }

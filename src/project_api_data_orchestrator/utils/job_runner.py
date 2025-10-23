import traceback
from datetime import datetime
from project_api_data_orchestrator.db.connection import get_connection

def create_job_record(job_name: str):
    conn = get_connection(DB_NAME='job_data')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orchestrator_jobs (job_name, status) VALUES (%s, %s) RETURNING id;",
        (job_name, 'pending')
    )
    job_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return job_id

def update_job_status(job_id: int, status: str, message: str = None):
    conn = get_connection(DB_NAME='job_data')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orchestrator_jobs SET status=%s, message=%s, completed_at=%s WHERE id=%s;",
        (status, message, datetime.now(), job_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def run_job_in_background(job_id: int, job_func):
    try:
        result = job_func.run()
        update_job_status(job_id, 'completed', result.get("message"))
    except Exception as e:
        traceback_str = traceback.format_exc()
        update_job_status(job_id, 'failed', traceback_str)

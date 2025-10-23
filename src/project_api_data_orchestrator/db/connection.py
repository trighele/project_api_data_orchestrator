import psycopg2
from psycopg2.extras import RealDictCursor
from project_api_data_orchestrator.core.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD

def get_connection(DB_NAME: str):
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

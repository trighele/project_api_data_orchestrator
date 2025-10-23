# 🧩 FastAPI Data Orchestrator

A modular **FastAPI** application for running **data orchestration jobs** (e.g., updating database tables, refreshing data, syncing APIs) via **HTTP API calls**.  
It’s designed to integrate seamlessly with tools like **n8n** or any other workflow automation system.

---

## 🚀 Features

- Expose orchestration jobs as REST API endpoints  
- Queue and track job execution using PostgreSQL  
- Asynchronous execution using FastAPI `BackgroundTasks`  
- Job results persisted with statuses: `pending`, `completed`, `failed`  
- Easily extensible — just drop new job scripts in `/app/jobs`  

---

## 📂 Folder Structure

fastapi_orchestrator/\
│\
├── app/\
│ ├── main.py # FastAPI entrypoint\
│ ├── api/\
│ │ └── jobs.py # Routes for job execution & status checks\
│ ├── core/\
│ │ └── config.py # Config (DB credentials, env vars)\
│ ├── db/\
│ │ ├── connection.py # psycopg2 connection utility\
│ │ └── schema.sql # Table creation for job tracking\
│ ├── jobs/\
│ │ ├── update_player_data.py # Example job 1\
│ │ └── update_player_stats.py # Example job 2\
│ └── utils/\
│ └── job_runner.py # Background job runner logic\
│\
├── requirements.txt\
└── README.md

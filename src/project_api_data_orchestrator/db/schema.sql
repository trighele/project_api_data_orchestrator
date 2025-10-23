CREATE TABLE IF NOT EXISTS orchestrator_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    message TEXT
);

FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /app

EXPOSE 8000

CMD ["uvicorn", "project_api_data_orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]
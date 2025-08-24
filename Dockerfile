FROM python:3.11-slim

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY app/ ./app/
COPY dagster-job/ ./dagster-job/

CMD ["dagster", "dev", "-h", "0.0.0.0", "-f", "dagster-job/dagster_pipeline.py"]

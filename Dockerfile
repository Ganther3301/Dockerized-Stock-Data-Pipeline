FROM python:3.11-slim

RUN pip install dagster dagit psycopg2-binary requests python-dotenv dagster-webserver yfinance

COPY main.py dagster_pipeline.py ./

CMD ["dagster", "dev", "-h", "0.0.0.0", "-f", "dagster_pipeline.py"]

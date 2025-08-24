from dagster import job, op, ScheduleDefinition, Definitions
from main import main


@op
def run_pipeline_op():
    """Op that calls the pipeline script"""
    success = main()
    if not success:
        raise Exception("Pipeline failed")


@job
def stock_job():
    """Dagster job that executes the pipeline"""
    run_pipeline_op()


stock_schedule = ScheduleDefinition(
    job=stock_job,
    cron_schedule="50 12 * * *",
    execution_timezone="Asia/Kolkata",
)

defs = Definitions(
    jobs=[stock_job],
    schedules=[stock_schedule],
)

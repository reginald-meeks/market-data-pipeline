from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/opt/airflow/src')

from ingestion.ingest import run_ingestion
from validation.validate import run_validation
from transform.transform import run_transform
from analytics.analytics import run_analytics

def on_failure_callback(context):
    print(f"Task failed: {context['task_instance'].task_id}")
    print(f"DAG: {context['task_instance'].dag_id}")
    print(f"Execution time: {context['execution_date']}")

default_args = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": on_failure_callback
}

with DAG(
    dag_id="market_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args = default_args
) as dag:
    ingest_task = PythonOperator(
        task_id="ingest",
        python_callable=run_ingestion,
        dag=dag
    )
    validate_task = PythonOperator(
        task_id="validate",
        python_callable=run_validation,
        dag=dag
    )
    transform_task = PythonOperator(
        task_id="transform",
        python_callable=run_transform,
        dag=dag
    )
    analytics_task = PythonOperator(
        task_id="analyze",
        python_callable=run_analytics,
        dag=dag
    )
    ingest_task >> validate_task >> transform_task >> analytics_task


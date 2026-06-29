from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

sys.path.insert(0, '/opt/airflow/src')

from ingestion.ingest import run_ingestion
from validation.validate import run_validation
from transform.transform import run_transform

with DAG(
    dag_id="market_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False
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
    ingest_task >> validate_task >> transform_task


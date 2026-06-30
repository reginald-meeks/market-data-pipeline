import psycopg2
from datetime import datetime

def log_metrics(dag_id, task_id, run_id, rows_processed,
                status, started_at, ended_at):

    duration_seconds = (ended_at - started_at).total_seconds()

    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        dbname="market_data",
        user="airflow",
        password="airflow"
    )

    cursor = conn.cursor()

    cursor.execute("""
                   INSERT INTO pipeline_metrics
                   (dag_id, task_id, run_id, rows_processed, status, started_at, ended_at, duration_seconds)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   """, (
                        dag_id,
                        task_id,
                        run_id,
                        rows_processed,
                        status,
                        started_at,
                        ended_at,
                        duration_seconds
                   ))

    conn.commit()
    cursor.close()
    conn.close()
    print("Metric logging complete.")

# Learning Log — Market Data Pipeline

## Progress
Day 1: Project setup, Docker Compose, Airflow + Postgres running, API verified
Day 2: Raw ingestion layer, Alpha Vantage to Postgres staging table
Day 3: Transformation layer — raw staging data cleaned and loaded into processed_market_data
Day 4: Data quality & validation layer — null, numeric, range, duplicate checks, quarantine table live
Day 5: Airflow DAG wired up, pipeline runs end to end — ingest → validate → transform
Day 6: DAG hardened — retries, failure handling, schedule confirmed
Day 7: Idempotent design — unique constraints, upserts, pipeline safely re-runnable
Day 8: Analytics layer — 7-day moving average computed and stored in market_analytics
Day 9: Logging + observability — pipeline_metrics table tracking duration, rows, and status per task



---

## Day 1
### What I built
Scaffolded full project structure in IntelliJ with Python 3.9 virtual environment.
Created folder structure: dags/, src/ingestion, src/transform, src/validation,
src/analytics, docs/, tests/. Wrote docker-compose.yml with four services: postgres,
airflow-webserver, airflow-scheduler, airflow-init — wired together using a YAML
anchor to avoid duplicating shared config. Used a Postgres init script to auto-create
the market_data database on first startup. Ran airflow-init successfully (exit code 0),
brought up webserver and scheduler, confirmed Airflow UI loads at localhost:8080.
Wrote first Python script to call Alpha Vantage API and verified live AAPL daily
pricing data returns correctly.

### What confused me
YAML indentation tripped me up — I nested services: inside the x-airflow-common
anchor instead of keeping it at the top level. The multiline > syntax for the
airflow-init command caused bash to treat each --flag as a separate command rather
than arguments, which caused a restart loop. Python was entirely new — no type
declarations, different import patterns, f-strings, and no prior reference point
for how any of it fits together. I also didn't understand what .venv was actually
doing or where pip install was putting packages.

### How I resolved it
Fixed the YAML structure by retyping the services block at the correct indentation
level — zero indent, same as version: and x-airflow-common:. Fixed the airflow-init
command by putting the entire bash command on one line, removing the multiline
ambiguity. Python syntax started clicking once Java equivalents were shown side by
side — seeing requests.get() next to Java's HttpClient setup made it clear why the
abstraction exists. Understood .venv as the Python equivalent of Maven managing
dependencies per project — packages install into .venv/lib/ rather than system-wide,
so projects stay isolated.

### Performance notes
Docker image pull (apache/airflow:2.8.1): ~24 seconds on first pull.
airflow-init: clean exit code 0.
Alpha Vantage API: returns 100 trading days of AAPL daily pricing.
All values returned as strings — type conversion needed in transform layer.
Field names have numbered prefixes ("1. open") — will need cleaning on Day 3.

---

## Day 2
### What I built
Created scripts/init_db.sql to auto-create the raw_market_data staging table in
Postgres on first startup — switched database context with \c market_data before
the CREATE TABLE statement. Wrote src/ingestion/ingest.py — loads the API key
from .env, calls Alpha Vantage for AAPL daily pricing, connects to Postgres via
psycopg2, and inserts each trading day as a row into raw_market_data. Verified
100 rows landed correctly by querying the table directly. Identified duplicate
insertion behavior — running the script twice produces 200 rows with no conflict
handling, which is an expected staging layer tradeoff to be hardened on Day 7.

### What confused me
Nothing blocked me today. psycopg2 mapped directly onto JDBC concepts I already
knew — connection, cursor, execute, commit, close. The Python syntax was easier
to follow once Java equivalents were shown side by side. The duplicate insertion
behavior was surprising at first but made sense once I understood the staging
table's role — raw data lands untouched, conflict handling comes later.

### How I resolved it
No major resolution needed. Understanding that the staging table is a raw landing
zone, not a source of truth, reframed the duplicate behavior from a bug to an
expected tradeoff. The fix is intentionally deferred to Day 7.

### Performance notes
100 rows inserted in a single script run — one row per trading day returned by
the API. Duplicate behavior confirmed: re-running without truncating doubles the
row count. No unique constraint on staging table by design — raw data lands
untouched, idempotency handled in Day 7. Table reset to 100 clean rows before
Day 3.

---

## Day 3
### What I built
Created processed_market_data table in init_db.sql with proper types — NUMERIC
for prices, BIGINT for volume, DATE for trade_date. Wrote src/transform/transform.py
using pandas and SQLAlchemy — reads 100 rows from raw_market_data into a DataFrame,
converts all price columns from TEXT to float, volume from TEXT to int, trade_date
to a proper datetime, drops the raw id column, and writes clean records into
processed_market_data. Verified data landed with correct types in Postgres.

### What confused me
Python syntax and functions were the main source of confusion throughout the day
since this is my first real Python project. The errors were the hardest part —
seeing a long stack trace with SQLAlchemy and psycopg2 internals mixed together
made it difficult to know where to even start reading. Without guidance I wouldn't
have known what the error was actually telling me versus what was noise.

### How I resolved it
Java equivalents helped ground the new syntax — seeing psycopg2 next to raw JDBC
and SQLAlchemy next to JdbcTemplate made the abstraction layers click. For the
errors, working through them with explanation of what each line meant helped
identify the actual cause rather than just the symptom. Going forward the goal
is to be able to read errors independently and trace them back to the source —
that's the skill that lets me say in an interview that I found it, debugged it,
and fixed it myself.

### Performance notes
100 rows read from staging, transformed in memory, written to processed table in
one script run. Type conversion confirmed — prices stored as NUMERIC, volume as
BIGINT, trade_date as DATE. SQLAlchemy required over raw psycopg2 for pandas
compatibility — psycopg2 handles direct SQL execution, SQLAlchemy provides the
standardized interface pandas expects.

---

## Day 4
### What I built
Added quarantine_market_data table to init_db.sql with TEXT columns for all price
and volume fields — stores bad records exactly as they came in without type casting.
Wrote src/validation/validate.py with four validation checks: null check (required
fields cannot be empty), numeric check (price and volume fields must be convertible
to float), range check (all prices and volume must be greater than 0), and duplicate
check (symbol + trade_date combination must be unique). Invalid records are tagged
with a reason and written to quarantine_market_data. Verified by injecting a
negative open price record — caught and quarantined correctly, 100 valid records
passed through cleanly.

### What confused me
Nothing significantly confused me today. The validation concepts were
straightforward and the pandas patterns from Day 3 carried over cleanly.
In hindsight the skeleton approach meant I wasn't writing enough Python
myself — changing that going forward.

### How I resolved it
N/A — no major blockers this session.

### Performance notes
100 valid records, 0 quarantined on clean Alpha Vantage data. Injected one bad
record (negative open price) — caught by range check, written to quarantine with
reason "failed validation", original bad value preserved as TEXT. Validation runs
in memory using pandas boolean masks — entire columns checked at once rather than
row by row.

---

## Day 5
### What I built
Created dags/market_pipeline_dag.py — defined a DAG with id "market_pipeline",
@daily schedule, catchup=False. Wrapped ingest.py, validate.py, and transform.py
logic into run_ingestion(), run_validation(), and run_transform() functions callable
by Airflow. Configured PythonOperator tasks for each stage and wired dependencies
with >> operator: ingest >> validate >> transform. Added _PIP_ADDITIONAL_REQUIREMENTS
to docker-compose.yml so Airflow containers install required packages on startup.
Updated all connection strings from localhost to postgres service name. Verified
full pipeline run via Airflow scheduler logs — all three tasks exited with code 0.

### What confused me
The Airflow UI was disorienting at first — Grid view, Graph view, task states,
run IDs, and log navigation are all new concepts with no prior reference point.
Triggering a run and knowing where to look for results wasn't intuitive. Reading
logs through the terminal ended up being clearer than hunting through the UI.

### How I resolved it
Switched to reading task logs directly via docker exec rather than navigating
the UI — that gave clean, readable output for each task. The UI made more sense
once the pipeline was actually running and I could see the three tasks lighting
up in the Graph view. Understanding came from seeing it work, not from the
interface itself.

### Performance notes
Full pipeline run duration: ~3 seconds end to end.
ingest: ~1s, validate: ~1s, transform: ~1s.
Scheduled run triggered automatically for 2026-06-28 on DAG unpause.
100 rows ingested, 100 validated, 100 transformed successfully.

---

## Day 6
### What I built
Hardened market_pipeline_dag.py with production-grade configuration. Added
default_args with retries=3 and retry_delay=5 minutes — transient failures
like API timeouts will retry automatically before marking a task failed.
Added on_failure_callback that logs the failed task id, DAG id, and execution
time when all retries are exhausted. Updated schedule_interval to schedule
to resolve Airflow 3 deprecation warning. Verified full pipeline run still
succeeds end to end after changes.

### What confused me
The placement of new components in the DAG file wasn't immediately obvious —
specifically where the failure callback function and default_args dictionary
should live relative to the DAG constructor and imports. Python file structure
is less rigid than Java class structure, so the conventions took a moment to
internalize.

### How I resolved it
Reasoned through it by thinking about Python's top-to-bottom execution order —
a function must be defined before it's referenced, and default_args must exist
before it's passed to the DAG constructor. Once I applied that mental model the
placement became logical rather than arbitrary.

### Performance notes
Full pipeline run: all three tasks succeeded, same ~3 second total duration.
Retries configured: 3 attempts, 5 minute delay between attempts.
on_failure_callback fires after all retries exhausted — not on first failure.

---

## Day 7
### What I built
Added unique constraints on (symbol, trade_date) to raw_market_data and
processed_market_data in init_db.sql — named uq_raw_symbol_date and
uq_processed_symbol_date. Updated ingest.py INSERT to use ON CONFLICT
(symbol, trade_date) DO NOTHING — duplicate records are skipped silently
rather than failing. Replaced df.to_sql() in transform.py with a manual
upsert loop using SQLAlchemy text() and ON CONFLICT DO NOTHING. Removed
load_dotenv() from all three pipeline scripts — Docker Compose injects
ALPHA_VANTAGE_API_KEY directly as an environment variable. Added
if __name__ == "__main__" blocks to all three scripts so they can be run
directly for testing. Verified idempotency — running ingest and transform
twice keeps row counts at exactly 100.

### What confused me
Three bugs slowed down Day 7. First, load_dotenv() was silently doing nothing
inside the container because the .env file wasn't at the path Python expected —
no error, just no API key. Second, running the scripts directly produced no output
because the functions were never actually called — Python loads the file, sees a
function definition, and exits without running anything. Third, conn.commit()
threw an AttributeError because SQLAlchemy 2.x Connection objects don't have a
commit() method directly.

### How I resolved it
For the dotenv issue — removed load_dotenv() entirely since Docker Compose already
injects the API key as an environment variable. For the silent script issue — added
if __name__ == "__main__" blocks so scripts can be run directly for testing without
affecting how Airflow imports them. For the commit issue — replaced conn.commit()
with conn.execute(text("COMMIT")) which works with SQLAlchemy's connection API.

### Performance notes
Idempotency verified: ingest run twice → 100 rows (not 200).
Transform run twice → 100 rows in processed_market_data (not 200).
ON CONFLICT DO NOTHING skips duplicates silently — no errors, no extra rows.
Full DAG run succeeded: all three tasks exit code 0.

---

## Day 8
### What I built
Added market_analytics table to init_db.sql with a composite unique constraint
on (symbol, trade_date). Wrote src/analytics/analytics.py — reads from
processed_market_data, computes a 7-day moving average using a SQL window
function (AVG OVER PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 6
PRECEDING AND CURRENT ROW), and writes results into market_analytics via
upsert. Wired run_analytics into the DAG as a fourth PythonOperator task,
extending the dependency chain to ingest >> validate >> transform >> analyze.
Verified 100 rows in market_analytics with correct moving averages.

### What confused me
Nothing significantly blocked me today. The window function syntax was new
but the concept clicked once I understood the sliding window model — average
of the current row and the 6 before it, recalculated for every date. The main
mistake was copying the INSERT from transform.py without updating the table
name and columns — caught it quickly once I compared the analytics table schema
against what I was inserting.

### How I resolved it
Tested the window function SQL directly in Postgres before writing any Python —
seeing the output confirmed the logic was right before wiring it into the script.
Fixed the INSERT by referencing market_analytics columns instead of
processed_market_data columns.

### Performance notes
100 rows computed and written to market_analytics in one script run.
Window function correctly handles edge cases — first row average equals its
own close price, full 7-day window kicks in at row 7.
All four DAG tasks succeeded: ingest → validate → transform → analyze.

---

## Day 9
### What I built
Created pipeline_metrics table in init_db.sql to store per-task run metadata.
Wrote src/utils.py with a log_metrics() function — takes dag_id, task_id,
run_id, rows_processed, status, started_at, ended_at, calculates duration_seconds
internally, and inserts one row into pipeline_metrics via psycopg2. Added
sys.path.insert to all four pipeline scripts so they can import utils.py from
the src/ parent directory. Wired log_metrics() into ingest, validate, transform,
and analytics — each captures started_at at function start and calls log_metrics
after completing its work. Verified two full pipeline runs produced 8 rows in
pipeline_metrics with correct durations and status.

### What confused me
The only friction today was the ModuleNotFoundError when importing utils —
Python looked for utils.py in the script's own directory rather than the
src/ parent directory. Not obvious until you hit the error.

### How I resolved it
Added sys.path.insert(0, '/opt/airflow/src') to each script so Python knows
to look in the src/ directory when resolving imports. Same pattern already
used in the DAG file — just needed to apply it consistently to the pipeline
scripts themselves.

### Performance notes
Two complete pipeline runs logged — 8 rows total in pipeline_metrics.
Ingest: ~0.4–0.5s (API call dominates). Validate: ~0.01–0.06s.
Transform: ~0.04–0.06s. Analytics: ~0.04–0.05s.
Ingest is consistently the slowest task due to the external API call —
all other stages are database-bound and complete in under 100ms.

---



---
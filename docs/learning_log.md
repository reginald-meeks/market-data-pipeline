# Learning Log — Market Data Pipeline

## Progress
Day 1: Project setup, Docker Compose, Airflow + Postgres running, API verified
Day 2: Raw ingestion layer, Alpha Vantage to Postgres staging table
Day 3: Transformation layer — raw staging data cleaned and loaded into processed_market_data
Day 4: Data quality & validation layer — null, numeric, range, duplicate checks, quarantine table live


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

### How I resolved it

### Performance notes
100 valid records, 0 quarantined on clean Alpha Vantage data. Injected one bad
record (negative open price) — caught by range check, written to quarantine with
reason "failed validation", original bad value preserved as TEXT. Validation runs
in memory using pandas boolean masks — entire columns checked at once rather than
row by row.

---



---
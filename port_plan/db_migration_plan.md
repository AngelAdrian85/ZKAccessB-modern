Set-Location 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB'
git checkout -b port/python3/commands-and-migrations
git add -A
git commit -m "port(commands+ci+db): modernize management commands, expand tests, improve CI, add DB migration plan"
git push -u origin port/python3/commands-and-migrations# DB migration plan — MySQL (legacy) -> PostgreSQL (target)

This document outlines a safe, incremental plan to migrate the legacy MySQL-based schema/data to PostgreSQL for use with the modernized Django app (Django 4.2).

Goals
- Extract schema and data from legacy MySQL with minimal downtime.
- Provide repeatable, tested migration steps.
- Address common incompatibilities (types, unsigned ints, collations, enum types, auto-increment behavior).

High-level approach
1. Inventory models/schema.
2. Export schema + sample data from MySQL.
3. Map MySQL types and constraints to PostgreSQL.
4. Create Django models (or adapt existing ones) and generate migrations for Postgres.
5. Load data into Postgres in a staging environment and validate.
6. Update application settings and cut over.

Step 1 — Inventory
- Use `SHOW TABLES;` and `SHOW CREATE TABLE <table>;` on legacy MySQL to get exact schema.
- Use `mysqldump --no-data` to export DDL as a starting point.
- Alternatively use `python manage.py inspectdb --database legacy` to produce Django models from the legacy DB (requires a Django settings entry pointing to the MySQL instance).

Commands (examples)

- Dump schema only (MySQL):
```bash
mysqldump -u root -p --no-data legacy_db > legacy_schema.sql
```

- Dump data for specific tables (sample):
```bash
mysqldump -u root -p --skip-lock-tables --single-transaction --quick legacy_db table1 table2 > sample_data.sql
```

- Use `inspectdb` to generate model stubs (helpful to create Django migrations):
```bash
# create a temporary Django settings entry pointing to legacy MySQL and run:
python manage.py inspectdb --database=legacy > legacy_models.py
```

Step 2 — Mapping notes (common issues)
- Unsigned integers: PostgreSQL doesn't have unsigned types. Map `INT unsigned` -> `BigIntegerField` or `PositiveIntegerField` and check max values.
- AUTO_INCREMENT vs SERIAL: Django migrations handle this normally, but verify primary key ranges.
- `ENUM` and `SET`: Convert to `CharField` with choices or a separate lookup table.
- `TEXT`/`BLOB` vs `bytea`: Map carefully; for binary blobs prefer `bytea` and update code handling bytes vs str.
- Character sets and collations: ensure MySQL `utf8mb4` -> Postgres `UTF8`. Convert text columns if necessary.
- `DATETIME` timezone handling: Postgres stores timestamps with/without time zone; prefer `timestamp with time zone` in Django when USE_TZ=True.
- Indexes and fulltext: MySQL fulltext indexes behave differently; consider using Postgres full-text search or external search engine (Elasticsearch/PGroonga) if needed.

Step 3 — Convert DDL
- Simple approach: Use `pgloader` to convert data/schema automatically:
```bash
pgloader mysql://user:pass@host/legacy_db postgresql://user:pass@host/new_db
```
pgloader handles many conversions (including charset, integer ranges) but review its output carefully.

- Manual approach (recommended for critical systems):
  - Create a new Postgres DB and reproduce schema using Django migrations (preferred).
  - If using Django models, create models that match expected types, run `python manage.py makemigrations` and `migrate` to create schema in Postgres.

Step 4 — Data migration
- For small datasets: export CSV from MySQL and import into Postgres using `COPY`.
- For larger datasets, use `pgloader` with tuned options, or build incremental ETL scripts (Python, pandas, or custom scripts) that transform and insert data.
- When inserting, consider disabling/rebuilding non-unique indexes after bulk load for performance.

Step 5 — Validation
- Run application test suite against the Postgres staging DB.
- Spot-check important tables and run SELECT counts to compare rows.
- Validate key application flows (login, admin, critical reports).

Step 6 — Cutover
- Choose a maintenance window.
- Stop writes to MySQL (put app in read-only mode or pause write workers).
- Do a final incremental sync (dump recent deltas or replay binlog) and load into Postgres.
- Switch application settings to use Postgres and restart services.

Rollback plan
- Keep the MySQL instance available as a fallback.
- Ensure backups and a tested restore process exist before cutover.

Tools & references
- pgloader — automated MySQL -> Postgres migrations.
- django-inspectdb — helpful to bootstrap model definitions from legacy DB.
- mysqldump / mysqlpump — export schema/data.
- psycopg2 / Django ORM — for custom ETL scripts.

Notes specific to this repo
- The codebase contains many legacy `.pyc` files and vendor modules under `zkeco/python-support`. Prioritize porting business-domain models first (those under `zkeco/units/*`) and test them against Postgres.
- We already switched dev to SQLite and added Postgres docker-compose; use the `docker-compose.yml` in the repo to create a local Postgres instance for staging.

Next concrete tasks
1. Run `inspectdb` against a MySQL copy and compare generated models with existing code.
2. Try `pgloader` on a snapshot to quickly see conversion issues.
3. Create a staging Postgres DB and run Django tests; iterate on model fixes.

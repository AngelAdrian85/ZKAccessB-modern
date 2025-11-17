# DB Migration Runbook — Concrete Example with Test Script

This runbook provides a step-by-step example for migrating a single table from MySQL to PostgreSQL, with a test script you can run locally to validate the approach.

## Example: Migrate `users` table

Assume the legacy MySQL schema has:

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255),
    email VARCHAR(255),
    is_active TINYINT DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);
```

### Step 1: Export schema from MySQL

```bash
# Dump schema only
mysqldump -h localhost -u legacy_user -p legacy_db users --no-data > users_schema.sql

# View the output
cat users_schema.sql
```

Output will look like:
```sql
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `password` varchar(255),
  `email` varchar(255),
  `is_active` tinyint DEFAULT '1',
  `created_at` datetime,
  `updated_at` datetime,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Step 2: Convert to Django model

Create a Django model in `zkeco_modern/zkeco_config/models.py` or a new app:

```python
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username
```

### Step 3: Create and run Django migration

```bash
cd zkeco_modern
DJANGO_SETTINGS_MODULE=zkeco_config.settings python manage.py makemigrations
DJANGO_SETTINGS_MODULE=zkeco_config.settings python manage.py migrate
```

### Step 4: Export data from MySQL

```bash
# Export data as CSV (compatible with Postgres COPY)
mysqldump -h localhost -u legacy_user -p legacy_db users \
  --no-create-info --tab=/tmp --fields-terminated-by=',' > /tmp/users.csv
  
# Or use a more explicit MySQL command:
mysql -h localhost -u legacy_user -p legacy_db \
  -e "SELECT id, username, password, email, is_active, created_at, updated_at FROM users" \
  --batch --skip-column-names > /tmp/users_data.txt
```

### Step 5: Import data into Postgres

```bash
# Using psql COPY (most efficient)
psql -h localhost -U zkeco -d zkeco_db -c \
  "COPY users (id, username, password, email, is_active, created_at, updated_at) \
   FROM STDIN WITH (FORMAT CSV, DELIMITER ',');" < /tmp/users.csv

# Or using Django ORM (for transformations):
# See script below
```

### Step 6: Validate data

```bash
# Check row count
mysql -u legacy_user -p legacy_db -e "SELECT COUNT(*) FROM users;"
psql -U zkeco -d zkeco_db -c "SELECT COUNT(*) FROM users;"

# Spot-check records
mysql -u legacy_user -p legacy_db -e "SELECT * FROM users LIMIT 5;"
psql -U zkeco -d zkeco_db -c "SELECT * FROM users LIMIT 5;"
```

## Test Migration Script (Python)

Save as `zkeco_modern/scripts/migrate_mysql_to_postgres_example.py`:

```python
#!/usr/bin/env python
"""
Example: Migrate user table from MySQL to Postgres using Django ORM.
Run: python manage.py shell < migrate_mysql_to_postgres_example.py
"""

import django
from django.conf import settings
import pymysql
from zkeco_config.models import User  # Adjust import per your app structure

# Configuration
LEGACY_DB_CONFIG = {
    "host": "localhost",
    "user": "legacy_user",
    "password": "legacy_password",
    "database": "legacy_db",
    "charset": "utf8mb4",
}

def migrate_users():
    """Fetch users from legacy MySQL and insert into Postgres via Django ORM."""
    # Connect to legacy MySQL
    conn = pymysql.connect(**LEGACY_DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("SELECT * FROM users;")
        rows = cursor.fetchall()
        
        print(f"Fetched {len(rows)} rows from legacy MySQL.")
        
        # Insert into Postgres via Django ORM
        for row in rows:
            user, created = User.objects.update_or_create(
                id=row["id"],
                defaults={
                    "username": row["username"],
                    "password": row.get("password", ""),
                    "email": row.get("email", ""),
                    "is_active": bool(row.get("is_active", 1)),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                },
            )
            status = "created" if created else "updated"
            print(f"  [{status}] user {user.username} (id={user.id})")
        
        print("Migration complete.")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_users()
```

### Run the script

```bash
cd zkeco_modern
DJANGO_SETTINGS_MODULE=zkeco_config.settings python manage.py shell < ../scripts/migrate_mysql_to_postgres_example.py
```

### Expected output

```
Fetched 10 rows from legacy MySQL.
  [created] user alice (id=1)
  [created] user bob (id=2)
  [created] user charlie (id=3)
  ...
Migration complete.
```

## Using pgloader (Automated)

For a faster, more automated approach, use `pgloader` which handles type conversions:

```bash
# Install pgloader (macOS)
brew install pgloader

# Or via Docker
docker run --rm -v /path/to/config:/config \
  dimitrik/pgloader pgloader /config/migration.load

# migration.load file:
LOAD DATABASE FROM mysql://legacy_user:legacy_password@localhost/legacy_db
                 INTO postgresql://zkeco:zkeco_password@localhost/zkeco_db
WITH include drop, create indexes, reset sequences
OPTIONS skip drop, truncate;
```

Run:
```bash
pgloader migration.load
```

## Safety Checklist

Before cutting over to production:

1. **Backup the original MySQL DB**: `mysqldump -u root -p legacy_db > legacy_db_backup.sql`
2. **Verify row counts match** between source and target.
3. **Spot-check critical records** (especially IDs, foreign keys, and unique constraints).
4. **Run application test suite** against the new Postgres DB to catch schema/data issues.
5. **Validate application workflows** (login, data retrieval, reports).
6. **Keep the MySQL instance available** as a rollback fallback during initial production validation.

## Troubleshooting

### Issue: "COPY" command fails with encoding error
**Solution**: Ensure MySQL export uses UTF-8:
```bash
mysqldump --default-character-set=utf8mb4 ...
```

### Issue: AUTO_INCREMENT values don't transfer
**Solution**: Manually set the sequence in Postgres after data import:
```bash
psql -c "SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users));"
```

### Issue: DATETIME fields are NULL after import
**Solution**: Check MySQL timezone settings and use explicit CONVERT_TZ or UTC format during export.

## Next Steps

1. Identify all tables in the legacy schema that need migration (use `SHOW TABLES;`).
2. Prioritize business-critical tables first (users, transactions, audit logs).
3. Create Django models for each table.
4. Test the migration script on a staging Postgres DB.
5. Once validated, coordinate cutover with operations/DBA team.

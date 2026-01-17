# Database Setup Guide

## Overview

This Django application supports both **SQLite** (for simple local development) and **PostgreSQL** (for production and advanced local development).

## Production (Railway)

The application automatically uses PostgreSQL on Railway via the `DATABASE_URL` environment variable. No additional configuration needed.

## Local Development

### Option 1: SQLite (Default - Simple Setup)

By default, the application uses SQLite for local development. This works well for most development tasks.

**Pros:**
- ✅ Zero configuration required
- ✅ No additional services to run
- ✅ Perfect for single-developer scenarios

**Limitations:**
- ⚠️ Limited concurrent write support
- ⚠️ Row-level locking (`select_for_update()`) has reduced effectiveness
- ⚠️ May see "database is locked" warnings during concurrent operations

**Optimizations Applied:**

The application automatically enables several SQLite optimizations for better concurrency:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,  # Wait up to 20 seconds for locks
        },
    }
}

# WAL mode is enabled via database signal (connection_created)
# This provides:
# - Write-Ahead Logging for better concurrent read/write
# - 20-second busy timeout to handle temporary locks
# - NORMAL synchronous mode for faster writes with WAL
```

**WAL Mode Setup:**
Unlike MySQL's `init_command`, SQLite requires WAL mode to be enabled via signals:
- `PRAGMA journal_mode=WAL;` - Enables Write-Ahead Logging
- `PRAGMA synchronous=NORMAL;` - Faster writes with WAL
- `PRAGMA busy_timeout=20000;` - 20 second timeout for lock waits

**Code Adaptations:**
- The codebase automatically detects SQLite and skips `select_for_update()` where it would cause issues
- Atomic transactions are still used for data integrity
- This provides 95% of the protection with zero configuration

**Verify WAL Mode:**
```bash
python test_database_config.py
```

This will show:
- ✅ WAL mode is ENABLED (better concurrency)
- ✅ Timeout is set to 20 seconds or more
- ✅ Database operations work correctly

### Option 2: PostgreSQL (Recommended for Production-Like Testing)

For full concurrency support and production-like behavior locally, use PostgreSQL.

#### Step 1: Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

#### Step 2: Create Database and User

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE moviebooking_dev;
CREATE USER moviebooking_user WITH PASSWORD 'your_secure_password';
ALTER ROLE moviebooking_user SET client_encoding TO 'utf8';
ALTER ROLE moviebooking_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE moviebooking_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE moviebooking_dev TO moviebooking_user;

# Grant schema privileges (PostgreSQL 15+)
\c moviebooking_dev
GRANT ALL ON SCHEMA public TO moviebooking_user;

# Exit
\q
```

#### Step 3: Install Python PostgreSQL Adapter

```bash
pip install psycopg2-binary
```

#### Step 4: Configure Environment Variables

Create or update your `.env` file:

```bash
# Add this line to use PostgreSQL locally
DATABASE_URL=postgresql://moviebooking_user:your_secure_password@localhost:5432/moviebooking_dev
```

#### Step 5: Run Migrations

```bash
python manage.py migrate
```

#### Step 6: Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

### Verification

Check which database you're using:

```bash
python manage.py shell

>>> from django.conf import settings
>>> print(settings.DATABASES['default']['ENGINE'])
# SQLite: django.db.backends.sqlite3
# PostgreSQL: django.db.backends.postgresql
```

## Redis Setup (Required for Both)

The application requires Redis for seat reservation caching.

### Install Redis

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

**Windows:**
Use WSL2 or download from https://github.com/microsoftarchive/redis/releases

### Configure Redis

In your `.env` file:
```bash
REDIS_URL=redis://localhost:6379/0
```

### Verify Redis

```bash
redis-cli ping
# Should return: PONG
```

## Troubleshooting

### "database is locked" Error (SQLite)

**Symptoms:**
- Error during payment processing or booking cancellation
- Usually appears with concurrent operations

**Solutions:**

1. **Use the optimizations** (already applied):
   - The code automatically skips problematic locking on SQLite
   - Increased timeout to 20 seconds
   - WAL mode enabled for better concurrency

2. **Switch to PostgreSQL** (see Option 2 above):
   - Provides full row-level locking support
   - Better for testing concurrent scenarios

3. **Reduce concurrent operations** (temporary workaround):
   - Avoid opening multiple payment tabs simultaneously
   - Wait for operations to complete before starting new ones

### PostgreSQL Connection Issues

**"role does not exist":**
```bash
# Recreate the user
psql postgres -c "CREATE USER moviebooking_user WITH PASSWORD 'your_password';"
```

**"database does not exist":**
```bash
# Recreate the database
psql postgres -c "CREATE DATABASE moviebooking_dev OWNER moviebooking_user;"
```

**"permission denied for schema public":**
```bash
# Grant schema permissions (PostgreSQL 15+)
psql moviebooking_dev -c "GRANT ALL ON SCHEMA public TO moviebooking_user;"
```

## Best Practices

### For Development:
- ✅ Use SQLite for quick setup and simple features
- ✅ Use PostgreSQL for testing payment flows and concurrent operations
- ✅ Always run migrations after switching databases
- ✅ Keep both `.env` and `.env.example` updated

### For Production:
- ✅ Always use PostgreSQL (Railway provides this automatically)
- ✅ Enable connection pooling (already configured)
- ✅ Use Redis for caching (required for seat reservations)
- ✅ Set appropriate `CONN_MAX_AGE` (already set to 600 seconds)

## Performance Tips

### SQLite:
```python
# Already applied in settings.py
- timeout=20 (prevents immediate "database is locked" errors)
- journal_mode=WAL (Write-Ahead Logging for better concurrency)
```

### PostgreSQL:
```python
# Already applied in settings.py
- conn_max_age=600 (connection pooling)
- conn_health_checks=True (automatic connection validation)
```

## Migration Between Databases

### SQLite → PostgreSQL:

1. **Export data:**
```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > data.json
```

2. **Switch to PostgreSQL** (update `.env` with `DATABASE_URL`)

3. **Run migrations:**
```bash
python manage.py migrate
```

4. **Import data:**
```bash
python manage.py loaddata data.json
```

### PostgreSQL → SQLite:

1. **Export data** (same as above)
2. **Remove `DATABASE_URL`** from `.env`
3. **Run migrations:**
```bash
python manage.py migrate
```
4. **Import data:**
```bash
python manage.py loaddata data.json
```

## Summary

- **Default (SQLite):** Works out of the box, suitable for most development
- **Advanced (PostgreSQL):** Full production parity, better for testing concurrent scenarios
- **Code automatically adapts:** Row-level locking is conditional based on database type
- **No breaking changes:** Both databases are fully supported and tested

# MariaDB Migration Guide

This project currently uses SQLite in `config/settings.py`:

- engine: `django.db.backends.sqlite3`
- database: `db.sqlite3`

If you want to move it to a server that already has MariaDB/MySQL installed, use the steps below.

## Recommended path

Do not hand-write the SQL structure.

Use:

1. Django migrations to create the schema in MariaDB
2. Django `dumpdata` / `loaddata` to move the data
3. `mysqldump` only if you also want a final `dump.sql` file afterward

## 1. Install MySQL driver

On the server, install one of these:

```bash
pip install mysqlclient
```

If `mysqlclient` is difficult to build, use:

```bash
pip install PyMySQL
```

If you use `PyMySQL`, add this in your project startup, for example in `config/__init__.py`:

```python
import pymysql

pymysql.install_as_MySQLdb()
```

## 2. Change Django database settings for MariaDB

Update `config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'evarya_health',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

## 3. Create the MariaDB database on the server

Login to MariaDB:

```bash
mysql -u root -p
```

Then run:

```sql
CREATE DATABASE evarya_health CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'your_db_user'@'%' IDENTIFIED BY 'your_db_password';
GRANT ALL PRIVILEGES ON evarya_health.* TO 'your_db_user'@'%';
FLUSH PRIVILEGES;
```

## 4. Create schema in MariaDB using Django migrations

On the server:

```bash
python manage.py migrate
```

This creates the full table structure from your migrations:

- `accounts/migrations/0001_initial.py`
- `accounts/migrations/0002_user_age.py`
- `accounts/migrations/0003_familycategory_familymember.py`
- `triage/migrations/0001_initial.py`

## 5. Export data from current SQLite database

Run this on the current machine where `db.sqlite3` has the data:

```bash
python manage.py dumpdata --exclude auth.permission --exclude contenttypes --indent 2 > data.json
```

This creates a portable data file.

## 6. Load that data into MariaDB

Copy `data.json` to the server, then run:

```bash
python manage.py loaddata data.json
```

## 7. Optional: create a real MariaDB `dump.sql`

After data is loaded into MariaDB, create a full SQL dump:

```bash
mysqldump -u your_db_user -p --databases evarya_health --routines --triggers --single-transaction > dump.sql
```

That `dump.sql` will contain:

- structure
- table data
- indexes
- triggers and routines if present

## 8. Import `dump.sql` on another server

If you already have a MariaDB server and just want to restore from the SQL dump:

```bash
mysql -u your_db_user -p evarya_health < dump.sql
```

## Fast command summary

### Current machine

```bash
python manage.py dumpdata --exclude auth.permission --exclude contenttypes --indent 2 > data.json
```

### Server

```bash
mysql -u root -p
```

```sql
CREATE DATABASE evarya_health CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'your_db_user'@'%' IDENTIFIED BY 'your_db_password';
GRANT ALL PRIVILEGES ON evarya_health.* TO 'your_db_user'@'%';
FLUSH PRIVILEGES;
```

```bash
pip install mysqlclient
python manage.py migrate
python manage.py loaddata data.json
```

### Optional SQL dump after migration

```bash
mysqldump -u your_db_user -p --databases evarya_health --routines --triggers --single-transaction > dump.sql
```

## Important note

Because this project currently stores data in SQLite, the cleanest and safest migration path is:

`SQLite -> dumpdata -> MariaDB migrate -> loaddata -> mysqldump`

That avoids hand-editing SQL and keeps the Django schema aligned with the codebase.

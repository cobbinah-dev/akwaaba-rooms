Alembic migration instructions

This project includes SQLAlchemy models. To use Alembic for migrations:

1. Install Alembic in your environment:

   pip install alembic

2. Initialize Alembic (one-time):

   alembic init migrations/alembic_env

3. Configure `alembic.ini` to point to your DB URL or set `sqlalchemy.url` in env.py.

4. In `env.py`, import your models so `target_metadata` references `models.Base.metadata`.

Example `env.py` snippet:

    from models import Base
    target_metadata = Base.metadata

5. Create an autogenerate revision after models change:

   alembic revision --autogenerate -m "Add hostels table"

6. Apply the migration:

   alembic upgrade head

Note: For simplicity this repo includes `migrations/ensure_hostel_table.py` which will create the `hostels` table directly using SQLAlchemy without Alembic. Use Alembic for production migration management and versioning.

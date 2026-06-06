#!/bin/bash
# setup.sh: Initialize database and assets before running Streamlit

mkdir -p assets/uploads
mkdir -p migrations/alembic/versions

echo "Initializing database..."
python -c "
from database import engine, init_db
from models import Base, Hostel
Base.metadata.create_all(bind=engine, tables=[Hostel.__table__])
print('✓ Database initialized.')
"

echo "Setup complete."

"""Ensure the `hostels` table exists by creating it from SQLAlchemy models.
Run: python migrations/ensure_hostel_table.py
"""
from database import engine
from models import Base, Hostel

if __name__ == '__main__':
    # create only the hostels table if it does not exist
    Base.metadata.create_all(bind=engine, tables=[Hostel.__table__])
    print('Hostels table ensured in database.')

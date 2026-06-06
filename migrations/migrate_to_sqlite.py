"""Simple migration helper: read JSON store and write a flat `hostels` table in SQLite.
Run: python migrations/migrate_to_sqlite.py
"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# prefer akwaaba_data.json, then data.json
json_paths = [ROOT / 'akwaaba_data.json', ROOT / 'data.json']
source = None
for p in json_paths:
    if p.exists():
        source = p
        break

if source is None:
    print('No JSON data file found.')
    exit(1)

with source.open('r', encoding='utf-8') as f:
    data = json.load(f)

# create sqlite
db_path = ROOT / 'akwaaba.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS hostels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    university_code TEXT,
    campus_name TEXT,
    name TEXT,
    description TEXT,
    price REAL,
    amenities TEXT,
    image_urls TEXT,
    gps_lat REAL,
    gps_lon REAL,
    available_slots INTEGER,
    room_types TEXT
)
''')

# flatten and insert
hostels_inserted = 0
for uni in data.get('universities', []):
    ucode = uni.get('code')
    for campus in uni.get('campuses', []):
        cname = campus.get('name')
        for hostel in campus.get('hostels', []):
            cur.execute('''INSERT INTO hostels (university_code,campus_name,name,description,price,amenities,image_urls,gps_lat,gps_lon,available_slots,room_types)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (
                ucode,
                cname,
                hostel.get('name'),
                hostel.get('description'),
                hostel.get('price'),
                json.dumps(hostel.get('amenities', [])),
                json.dumps(hostel.get('image_urls', []) or hostel.get('image_paths', [])),
                (hostel.get('gps_coordinates') or {}).get('latitude'),
                (hostel.get('gps_coordinates') or {}).get('longitude'),
                hostel.get('available_slots', 0),
                json.dumps(hostel.get('room_types', [])),
            ))
            hostels_inserted += 1

conn.commit()
conn.close()
print(f'Migration complete: inserted {hostels_inserted} hostels into {db_path}')

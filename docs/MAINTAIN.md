Akwaaba Rooms — Maintenance Notes

1) Data schema (JSON)
- Root object: { "universities": [ { "code", "name", "campuses": [ { "name", "gps_coordinates": {"latitude", "longitude"}, "hostels": [ { "name", "description", "price", "amenities": [..], "image_urls": [..], "room_types": [{"type","price","available"}], "available_slots", "gps_coordinates" } ] } ] } ] }

2) Recommended migration to SQLite
- A helper script `migrations/migrate_to_sqlite.py` converts the flattened hostels into a `hostels` table.
- Run: `python migrations/migrate_to_sqlite.py` then use `sqlite3 akwaaba.db` or an ORM to query.

3) Admin uploads
- Uploaded images are saved to `assets/uploads/` and the JSON stores the file paths in `image_paths` and `image_urls`.
- To scale: consider serving images from object storage (S3) and storing remote URLs instead of local files.

4) Adding fields
- New hostel fields: `price` (number), `amenities` (list of strings), `image_urls` (list of strings).
- Keep backwards compatibility: `image_paths` is honored if present.

5) Scaling notes
- Move from flat JSON to a proper DB when concurrent edits or many records are expected.
- Use SQLAlchemy models and Alembic for migrations when switching to SQLite/Postgres.
- Add unit tests around `akwaaba_store` CRUD operations and `migrations`.

6) Next steps (suggested)
- Implement an API layer (FastAPI) to serve hostels and images.
- Add pagination, filtering (price, amenities), and search.
- Add tests and CI to validate migrations and admin flows.

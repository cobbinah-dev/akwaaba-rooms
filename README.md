# Akwaaba Rooms 🇬🇭

A nationwide hostel search platform for Ghana. Browse universities, select a campus, view nearby hostels on a map, and use AI to search across all available options.

**Features:**
- 🗺️ Interactive maps with nearby hostels
- 🤖 AI-powered search across all platforms
- 👨‍💼 Admin panel to manage universities, campuses, and hostels
- 📸 Image uploads and amenities management
- 💰 Price filtering and room type details
- 📍 GPS-based location tracking

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.9+
- pip or conda

### Installation

1. **Clone & setup:**
   ```bash
   git clone https://github.com/cobbinah-dev/akwaaba-rooms.git
   cd akwaaba-rooms
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Initialize database:**
   ```bash
   python -c "from database import engine; from models import Base, Hostel; Base.metadata.create_all(bind=engine, tables=[Hostel.__table__]); print('✓ DB initialized')"
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Run the AI Assistant (separate terminal):**
   ```bash
   streamlit run app_ai.py
   ```

The app will open at `http://localhost:8501`.

---

## Project Structure

```
akwaaba-rooms/
├── app.py                      # Main Streamlit app (Explore + Admin modes)
├── app_ai.py                   # Separate AI Assistant app
├── ai_agent.py                 # Lightweight AI search engine
├── akwaaba_store.py            # JSON-based hostel store
├── models.py                   # SQLAlchemy models (Hostel, Block, Room, etc.)
├── database.py                 # DB connection and init
├── crud.py, store.py           # Utility modules
├── assets/
│   ├── ghana_flag.svg          # App icon/favicon
│   └── uploads/                # User-uploaded hostel images
├── migrations/
│   ├── migrate_to_sqlite.py    # JSON → SQLite migration
│   ├── ensure_hostel_table.py  # Create hostels table
│   └── alembic/README.md       # Alembic setup instructions
├── docs/MAINTAIN.md            # Maintenance guide
├── requirements.txt            # Python dependencies
├── Procfile                    # Heroku deployment config
├── setup.sh                    # Database initialization script
└── .gitignore
```

---

## Data Management

### JSON Store (Default)
- **File:** `akwaaba_data.json`
- **Format:** Nested universities → campuses → hostels
- **Use case:** Development, small deployments

**Schema:**
```json
{
  "universities": [
    {
      "code": "TTU",
      "name": "University Name",
      "campuses": [
        {
          "name": "Campus Name",
          "gps_coordinates": {"latitude": 4.8933, "longitude": -1.7652},
          "hostels": [
            {
              "name": "Hostel Name",
              "description": "...",
              "price": 1200,
              "amenities": ["WiFi", "AC"],
              "image_urls": ["url1.jpg"],
              "room_types": [{"type": "Single", "price": 1200, "available": 2}],
              "available_slots": 4,
              "gps_coordinates": {...}
            }
          ]
        }
      ]
    }
  ]
}
```

### SQLite (Recommended for Scale)

1. **Migrate JSON to SQLite:**
   ```bash
   python migrations/migrate_to_sqlite.py
   ```
   Creates `akwaaba.db` with a flattened `hostels` table.

2. **Ensure table exists:**
   ```bash
   python migrations/ensure_hostel_table.py
   ```

3. **Query the DB:**
   ```bash
   sqlite3 akwaaba.db
   sqlite> SELECT name, price, available_slots FROM hostels LIMIT 5;
   ```

### Alembic Migrations (Production)

For version-controlled schema changes:

1. **Install Alembic:**
   ```bash
   pip install alembic
   ```

2. **Initialize:**
   ```bash
   alembic init migrations/alembic_env
   ```

3. **Configure `alembic.ini` and `env.py` to use your DB URL.**

4. **Create & apply migrations:**
   ```bash
   alembic revision --autogenerate -m "Add hostels"
   alembic upgrade head
   ```

See [migrations/alembic/README.md](migrations/alembic/README.md) for details.

---

## Deployment

### Option 1: Streamlit Cloud (Easiest)

1. **Push to GitHub:**
   ```bash
   git push origin main
   ```

2. **Go to [streamlit.io/cloud](https://streamlit.io/cloud) and connect your repo.**

3. **Set secrets (if needed) in `.streamlit/secrets.toml`:**
   ```toml
   database_url = "sqlite:///akwaaba.db"
   ```

4. **Deploy with one click.**

### Option 2: Heroku

1. **Install Heroku CLI:**
   ```bash
   brew tap heroku/brew && brew install heroku
   heroku login
   ```

2. **Create & deploy:**
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

3. **The `Procfile` and `setup.sh` handle database init automatically.**

### Option 3: Railway / Render / Fly.io

All support `requirements.txt` + `Procfile`. Push your repo and they'll auto-detect and deploy.

---

## Admin Panel Usage

1. Open the app and select **"Admin"** from the sidebar.
2. **Add University:** Enter university code and name.
3. **Add Campus:** Select university, enter campus name, GPS coords.
4. **Add Hostel:** Select university + campus, fill in:
   - Hostel name, description, price
   - Amenities (comma-separated)
   - Rules (one per line)
   - Room types (format: `Single:1200:2` = type, price, available)
   - GPS coordinates
   - Upload hostel images (PNG, JPG, SVG)

All data is saved to JSON and SQLite (if using DB).

---

## AI Assistant

Ask natural language queries to search hostels:

- **Query examples:**
  - "Hostels with WiFi under 1500 GHS"
  - "Legon cheap rooms with kitchen"
  - "KNUST accommodation under 2000"

The AI agent:
1. Parses price ranges, amenities, and location hints.
2. Scores hostels based on match.
3. Returns ranked results with score.

**Run separately:**
```bash
streamlit run app_ai.py
```

---

## Environment Variables (Optional)

Create `.env` (not tracked by git):
```bash
DATABASE_URL=sqlite:///akwaaba.db
STREAMLIT_SERVER_PORT=8501
DEBUG=False
```

Load in your startup script:
```bash
source .env
streamlit run app.py
```

---

## Troubleshooting

### Database not found
```bash
python migrations/ensure_hostel_table.py
```

### Import errors
```bash
pip install --upgrade -r requirements.txt
```

### Images not showing
- Ensure `assets/uploads/` exists.
- Check image URLs are absolute or stored correctly.

### Port already in use
```bash
streamlit run app.py --server.port 8502
```

---

## Maintenance & Scaling

### Adding Fields
1. Update `models.py` with new SQLAlchemy column.
2. Create an Alembic migration: `alembic revision --autogenerate -m "Add field_name"`.
3. Apply: `alembic upgrade head`.

### Migrating to PostgreSQL
1. Update `DATABASE_URL` in `database.py`.
2. Install `psycopg2`: `pip install psycopg2-binary`.
3. Run Alembic migrations: `alembic upgrade head`.

### Performance
- Index frequently-queried columns (e.g., `university_code`, `campus_name`).
- Use pagination and filtering in `ai_agent.py` for large datasets.
- Cache folium maps with `@st.cache_resource`.

### Monitoring
- Log errors and queries in production.
- Set up uptime monitoring (UptimeRobot, New Relic).
- Monitor DB size and disk usage.

---

## Contributing

1. Fork the repo.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Commit & push: `git push origin feature/your-feature`.
4. Open a pull request.

---

## License

MIT License — see LICENSE for details.

---

## Support

For issues, email **support@akwaaba-rooms.dev** or open an issue on GitHub.

**Akwaaba Rooms** — Bringing students and hostels together. 🇬🇭

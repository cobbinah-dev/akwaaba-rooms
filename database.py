from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///hostel.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
# Use modern sessionmaker parameters: avoid unsupported `autocommit`
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

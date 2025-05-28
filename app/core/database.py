from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path
from app.core.settings import settings
import os
import logging

logger = logging.getLogger(__name__)

# Try to use the configured path, fall back to user's home directory if not accessible
try:
    db_path = Path(settings.DATABASE.SQLITE_PATH)
    logger.info(f"Attempting to create database at: {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Fall back to user's home directory
    db_path = Path.home() / "medialab-manager" / "medialab.db"
    logger.info(f"Permission denied, falling back to: {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)

# Database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
logger.info(f"Using database URL: {SQLALCHEMY_DATABASE_URL}")

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=True  # Enable SQL logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path
from app.core.settings import settings
import os
import logging
from typing import Optional, TypeVar, Generic, Type, Any

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
    echo=False  # Enable SQL logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Type variable for generic model type
T = TypeVar('T', bound=Base)

class DBManager(Generic[T]):
    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def create(self, **kwargs) -> T:
        """Create a new record"""
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, id: int) -> Optional[T]:
        """Get a record by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update a record by ID"""
        db_obj = self.get(id)
        if db_obj:
            for key, value in kwargs.items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def list(self, **filters) -> list[T]:
        """List records with optional filters"""
        query = self.db.query(self.model)
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, str):
                    query = query.filter(getattr(self.model, key).ilike(f"%{value}%"))
                else:
                    query = query.filter(getattr(self.model, key) == value)
        return query.all()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
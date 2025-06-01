from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path
from app.core.settings import settings
import os
import logging
from typing import Optional, TypeVar, Generic, Type, Any

logger = logging.getLogger(__name__)

def setup_database(db_path: str) -> tuple[create_engine, sessionmaker, declarative_base]:
    """Setup a database with the given path"""
    try:
        path = Path(db_path)
        logger.info(f"Attempting to create database at: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # Fall back to user's home directory
        path = Path.home() / "medialab-manager" / Path(db_path).name
        logger.info(f"Permission denied, falling back to: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)

    # Database URL
    database_url = f"sqlite:///{path}"
    logger.info(f"Using database URL: {database_url}")

    # Create engine
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=False
    )

    # Create SessionLocal class
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create Base class
    Base = declarative_base()

    return engine, SessionLocal, Base

# Setup main database
main_engine, MainSessionLocal, MainBase = setup_database(settings.DATABASE.MAIN_DB_PATH)

# Setup media database
media_engine, MediaSessionLocal, MediaBase = setup_database(settings.DATABASE.MEDIA_DB_PATH)

# Type variable for generic model type
T = TypeVar('T', bound=MainBase)
M = TypeVar('M', bound=MediaBase)

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

class MediaDBManager(Generic[M]):
    def __init__(self, model: Type[M], db: Session):
        self.model = model
        self.db = db

    def create(self, **kwargs) -> M:
        """Create a new record"""
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, id: int) -> Optional[M]:
        """Get a record by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def update(self, id: int, **kwargs) -> Optional[M]:
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

    def list(self, **filters) -> list[M]:
        """List records with optional filters"""
        query = self.db.query(self.model)
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, str):
                    query = query.filter(getattr(self.model, key).ilike(f"%{value}%"))
                else:
                    query = query.filter(getattr(self.model, key) == value)
        return query.all()

# Dependencies to get DB sessions
def get_db():
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_media_db():
    db = MediaSessionLocal()
    try:
        yield db
    finally:
        db.close() 
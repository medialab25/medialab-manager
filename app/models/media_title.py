from datetime import UTC, datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import MediaBase
import enum

class QualityLevel(int, enum.Enum):
    UHD = 50  # 4K
    FHD = 40  # 1080p
    HD = 30   # 720p
    SD = 20   # 480p
    LD = 10   # 360p
    UNKNOWN = 0

class MediaType(enum.Enum):
    MOVIE = "movie"
    TV_SHOW = "tv_show"

class MediaFileType(enum.Enum):
    OTHER = "other"
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"

class MediaTitle(MediaBase):
    __tablename__ = 'media_titles'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    # Relationships
    media_files = relationship("MediaFile", back_populates="media_title")
    # metadata = relationship("MediaMetadata", back_populates="media_title")

    def __repr__(self):
        return f"<MediaTitle(id={self.id}, title='{self.title}', type='{self.media_type}')>"

class MediaFile(MediaBase):
    __tablename__ = 'media_files'

    id = Column(Integer, primary_key=True, index=True)
    media_title_id = Column(Integer, ForeignKey('media_titles.id'))
    media_title = relationship("MediaTitle", back_populates="media_files")
    media_locations = relationship("MediaLocation", back_populates="media_file")
    media_file_type = Column(Enum(MediaFileType), nullable=False)

    # TV Show specific fields - only used when media_title.media_type is TV_SHOW
    season = Column(Integer, nullable=True)
    episode = Column(Integer, nullable=True)
    quality = Column(Enum(QualityLevel), nullable=True, default=QualityLevel.UNKNOWN)

    file_path = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    def __repr__(self):
        return f"<MediaFile(id={self.id}, media_title_id={self.media_title_id})>"

class MediaFolder(MediaBase):
    __tablename__ = 'media_folders'

    id = Column(Integer, primary_key=True, index=True)
    media_file_id = Column(Integer, ForeignKey('media_files.id'))
    media_file = relationship("MediaFile", back_populates="media_folders")

    media_type = Column(Enum(MediaType), nullable=False)
    media_quality = Column(Enum(QualityLevel), nullable=False)

    # Files in the folder
    # Titles in the folder
    # Cache Control

    folder_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

# class MediaFolderToFile -> MediaFile
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

class CacheStatus(enum.Enum):
    NONE = "none"
    MANUAL = "manual"

class PendingStatus(enum.Enum):
    NONE = "none"
    PROMOTE = "promote"
    DEMOTE = "demote"

class MediaFileType(enum.Enum):
    OTHER = "other"
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"

class FolderType(enum.Enum):
    CACHE = "cache"
    MERGE = "merge"
    SOURCE = "source"

class MediaTitle(MediaBase):
    __tablename__ = 'media_titles'

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    media_source_items = relationship("MediaSourceItem", back_populates="media_title")

    # Data
    title = Column(String(255), nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)

    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))


class MediaSourceItem(MediaBase):
    __tablename__ = 'media_source_items'

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    media_title_id = Column(Integer, ForeignKey('media_titles.id'))
    media_title = relationship("MediaTitle", back_populates="media_source_items")

    source_folder_group_id = Column(Integer, ForeignKey('media_folder_groups.id'))
    source_folder_group = relationship("MediaFolderGroup", back_populates="media_source_items")

    # Data
    quality = Column(Enum(QualityLevel), nullable=False)
    season = Column(Integer, nullable=True)
    episode = Column(Integer, nullable=True)
    source_files = relationship("MediaSourceFile", back_populates="media_source_item")
    cache_status = Column(Enum(CacheStatus), nullable=False)
    pending = Column(Enum(PendingStatus), nullable=False)

class MediaSourceFile(MediaBase):
    __tablename__ = 'media_source_files'

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    media_source_item_id = Column(Integer, ForeignKey('media_source_items.id'))
    media_source_item = relationship("MediaSourceItem", back_populates="source_files")

    cache_folder_group_id = Column(Integer, ForeignKey('media_folder_groups.id'))
    cache_folder_group = relationship("MediaFolderGroup", back_populates="source_files")

    # Data
    relative_title_path = Column(String(255), nullable=False)
    file_type = Column(Enum(MediaFileType), nullable=False)
    file_attributes = Column(String(255), nullable=False)
    cache_status = Column(Enum(CacheStatus), nullable=False)
    
    linked_files = relationship("MediaLinkedFile", back_populates="source_file")    

class MediaLinkedFile(MediaBase):
    __tablename__ = 'media_linked_files'

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    source_folder_group_id = Column(Integer, ForeignKey('media_folder_groups.id'))
    source_folder_group = relationship("MediaFolderGroup", backref="source_linked_files", secondary="media_linked_files")

    target_folder_group_id = Column(Integer, ForeignKey('media_folder_groups.id')) 
    target_folder_group = relationship("MediaFolderGroup", backref="target_linked_files", secondary="media_linked_files")


class MediaFolderGroup(MediaBase):
    __tablename__ = 'media_folder_groups'

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    source_linked_files = relationship("MediaLinkedFile", backref="source_folder_group", secondary="media_linked_files")
    target_linked_files = relationship("MediaLinkedFile", backref="target_folder_group", secondary="media_linked_files")
    media_source_items = relationship("MediaSourceItem", back_populates="media_folder_group")

    # Data
    base_path = Column(String(255), nullable=False)
    type = Column(Enum(FolderType), nullable=False)


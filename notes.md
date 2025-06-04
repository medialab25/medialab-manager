# DB Test

## Data
- StorageGroup is source/cache/merged etc

TitleName, Quality, AbsoluteFilePath, Season/Episode, MediaType, Library, CacheStatus, StorageGroup, FileParent, FileType

| TitleName | Quality | AbsoluteFilePath                          | Season/Episode | MediaType | Library | CacheStatus | StorageGroup | FileParent | FileType |RelFilePath|
|-----------|---------|-------------------------------------------|----------------|-----------|---------|-------------|--------------|------------|----------|-----------|
| YStone    | hd      | /srv/storage/media/tv-hd/YStone/ep1.mkv   | S01E02         | tv        | source  | incache     | tv-hd        | None       | Video    | Ystone/ep1.mkv|
| YStone    | uhd     | /srv/storage/media/tv-uhd/YStone/ep1u.mkv | S01E02         | tv        | source  | notcache    | tv-uhd       | None       | Video    | Ystone/ep1u.mkv|
| YStone    | hd      | /srv/storage/media/cache/YStone/ep1.mkv   | S01E02         | tv        | cache   | na          | cache        | 1          | Video    | Ystone/ep1.mkv|
| YStone    | hd      | /srv/storage/media/tv-hd/YStone/ep1.mkv   | S01E02         | tv        | merged  | na          | merged       | 3          | Video    | Ystone/ep1.mkv|


MediaTitle
- id
- name

MediaItem     # The data source version
- id
- link(title)
- quality
- link(source_file)
- season/episode
- cachestatus?
????- link(storage_groups)
- linked_files

MediaStorageGroup
- id
- name (tv-uhd/cache)
- path
- attributes

MediaFile
- id
- abspath
- size
- other_attributes
- type (video/other)

MediaFileLink
- id
- source_file
- target_file
- link_type


###

MediaSourcePath:
- id
- storage_group
- source_file: link(MediaFilePath)              # Physical location
- linked_files: many link(MediaFilePaths)       # Merged

MediaFilePath:
- id
- absolute_file_path

MediaCacheFile:
- id
- cache_provider_id: MANUAL/EPISODE-CACHE etc
- link(MediaSourcePath)

###

#### Logical

MediaTitle
- id
- media_type
- name

MediaSourceItem     # The data source version
- id
- link(title)
- source_folder_id: tv-hd
- quality
- season/episode
- source_files: link(*MediaSourceFile)     # All files associated with this item in cold storage e.g. mkv, srt, .txt
- cache_status: MANUAL/AUTO
- pending: UP/DOWN/NONE

MediaSourceFile:  # Single File
- id
- relative_title_path: str(256)
- file_type e.g. video/subtitle
- file_attributes e.g. size/updated
- cache_status: MANUAL/NONE/NA
#- cache_folder_id: tv-cached
- linked_files:

MediaLinkedFile:
- src_folder_id  media-cache -> media-cache-merged
- dest_folder_id

MediaFolderGroup: # Populated from config
- id
- base_path
- type



- folder_id: tv-hd etc.

- file_path: link(MediaFile)
- cache_file_path: link(MediaFile)


#### Physical:

MediaFile:
- id
- folder_id (tv-hd/tv-uhd)
- abs_path
- linked_files (e.g. merge)

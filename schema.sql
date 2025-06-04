/*
Database Schema Documentation

This database schema is designed to track media files across different storage locations and libraries.
The schema is normalized to reduce redundancy and maintain data integrity.

Table Relationships:
-------------------
MediaFiles (Main Table)
  ├── MediaTitles (One-to-Many)
  ├── Qualities (One-to-Many)
  ├── MediaTypes (One-to-Many)
  ├── Libraries (One-to-Many)
  ├── StorageGroups (One-to-Many)
  └── FileTypes (One-to-Many)

Table Descriptions:
------------------
1. MediaTitles
   - Stores unique media titles
   - Primary key: title_id
   - Example: "YStone"

2. StorageGroups
   - Defines different storage locations
   - Primary key: storage_group_id
   - Examples: tv-hd, tv-uhd, cache, merged

3. Libraries
   - Defines different library types
   - Primary key: library_id
   - Examples: source, cache, merged

4. MediaTypes
   - Defines types of media
   - Primary key: media_type_id
   - Example: tv

5. Qualities
   - Defines quality levels
   - Primary key: quality_id
   - Examples: hd, uhd

6. FileTypes
   - Defines file types
   - Primary key: file_type_id
   - Example: Video

7. MediaFiles
   - Main table storing all file information
   - Links to all other tables via foreign keys
   - Stores file paths, cache status, and relationships
   - file_parent references another MediaFiles record for hierarchical relationships

Example Query:
-------------
To find all HD versions of a show in the source library:
SELECT mf.*, mt.title_name, q.quality_name, l.library_name
FROM MediaFiles mf
JOIN MediaTitles mt ON mf.title_id = mt.title_id
JOIN Qualities q ON mf.quality_id = q.quality_id
JOIN Libraries l ON mf.library_id = l.library_id
WHERE mt.title_name = 'YStone'
AND q.quality_name = 'hd'
AND l.library_name = 'source';
*/

-- Create MediaTitles table
CREATE TABLE MediaTitles (
    title_id SERIAL PRIMARY KEY,
    title_name VARCHAR(255) NOT NULL
);

-- Create StorageGroups table
CREATE TABLE StorageGroups (
    storage_group_id SERIAL PRIMARY KEY,
    storage_group_name VARCHAR(50) NOT NULL
);

-- Create Libraries table
CREATE TABLE Libraries (
    library_id SERIAL PRIMARY KEY,
    library_name VARCHAR(50) NOT NULL
);

-- Create MediaTypes table
CREATE TABLE MediaTypes (
    media_type_id SERIAL PRIMARY KEY,
    media_type_name VARCHAR(50) NOT NULL
);

-- Create Qualities table
CREATE TABLE Qualities (
    quality_id SERIAL PRIMARY KEY,
    quality_name VARCHAR(50) NOT NULL
);

-- Create FileTypes table
CREATE TABLE FileTypes (
    file_type_id SERIAL PRIMARY KEY,
    file_type_name VARCHAR(50) NOT NULL
);

-- Create MediaFiles table (main table)
CREATE TABLE MediaFiles (
    file_id SERIAL PRIMARY KEY,
    title_id INTEGER REFERENCES MediaTitles(title_id),
    quality_id INTEGER REFERENCES Qualities(quality_id),
    absolute_file_path VARCHAR(1000) NOT NULL,
    season_episode VARCHAR(20),
    media_type_id INTEGER REFERENCES MediaTypes(media_type_id),
    library_id INTEGER REFERENCES Libraries(library_id),
    cache_status VARCHAR(50),
    storage_group_id INTEGER REFERENCES StorageGroups(storage_group_id),
    file_parent INTEGER,
    file_type_id INTEGER REFERENCES FileTypes(file_type_id),
    rel_file_path VARCHAR(1000) NOT NULL
);

-- Insert sample data for lookup tables
INSERT INTO StorageGroups (storage_group_name) VALUES 
    ('tv-hd'),
    ('tv-uhd'),
    ('cache'),
    ('merged');

INSERT INTO Libraries (library_name) VALUES 
    ('source'),
    ('cache'),
    ('merged');

INSERT INTO MediaTypes (media_type_name) VALUES 
    ('tv');

INSERT INTO Qualities (quality_name) VALUES 
    ('hd'),
    ('uhd');

INSERT INTO FileTypes (file_type_name) VALUES 
    ('Video');

-- Insert sample data for MediaTitles
INSERT INTO MediaTitles (title_name) VALUES 
    ('YStone');

-- Insert sample data for MediaFiles
INSERT INTO MediaFiles (
    title_id,
    quality_id,
    absolute_file_path,
    season_episode,
    media_type_id,
    library_id,
    cache_status,
    storage_group_id,
    file_parent,
    file_type_id,
    rel_file_path
) VALUES 
    (1, 1, '/srv/storage/media/tv-hd/YStone/ep1.mkv', 'S01E02', 1, 1, 'incache', 1, NULL, 1, 'Ystone/ep1.mkv'),
    (1, 2, '/srv/storage/media/tv-uhd/YStone/ep1u.mkv', 'S01E02', 1, 1, 'notcache', 2, NULL, 1, 'Ystone/ep1u.mkv'),
    (1, 1, '/srv/storage/media/cache/YStone/ep1.mkv', 'S01E02', 1, 2, 'na', 3, 1, 1, 'Ystone/ep1.mkv'),
    (1, 1, '/srv/storage/media/tv-hd/YStone/ep1.mkv', 'S01E02', 1, 3, 'na', 4, 3, 1, 'Ystone/ep1.mkv'); 
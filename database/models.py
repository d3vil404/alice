import json
from typing import Dict, List, Optional
from datetime import datetime

class DatabaseTables:
    """Class containing SQL commands for creating database tables"""
    
    @staticmethod
    def get_users_table() -> str:
        """Returns SQL command for creating users table"""
        return """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

    @staticmethod
    def get_playlists_table() -> str:
        """Returns SQL command for creating playlists table"""
        return """
        CREATE TABLE IF NOT EXISTS playlists (
            playlist_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            playlist_name VARCHAR(255),
            songs JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE KEY unique_playlist (user_id, playlist_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

    @staticmethod
    def get_admins_table() -> str:
        """Returns SQL command for creating admins table"""
        return """
        CREATE TABLE IF NOT EXISTS admins (
            admin_id BIGINT PRIMARY KEY,
            user_id BIGINT,
            promoted_by BIGINT,
            privileges JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

    @staticmethod
    def get_groups_table() -> str:
        """Returns SQL command for creating groups table"""
        return """
        CREATE TABLE IF NOT EXISTS groups (
            group_id BIGINT PRIMARY KEY,
            group_name VARCHAR(255),
            added_by BIGINT,
            is_active BOOLEAN DEFAULT TRUE,
            member_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (added_by) REFERENCES users(user_id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

    @staticmethod
    def get_active_streams_table() -> str:
        """Returns SQL command for creating active streams table"""
        return """
        CREATE TABLE IF NOT EXISTS active_streams (
            stream_id INT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT,
            current_song VARCHAR(255),
            requested_by BIGINT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE,
            FOREIGN KEY (requested_by) REFERENCES users(user_id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

class User:
    """User model for database operations"""
    def __init__(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    @staticmethod
    def create_user(cursor, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Create a new user in the database"""
        try:
            sql = """
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name)
            """
            cursor.execute(sql, (user_id, username, first_name, last_name))
            return True
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return False

class Playlist:
    """Playlist model for database operations"""
    def __init__(self, user_id: int, playlist_name: str, songs: List[Dict] = None):
        self.user_id = user_id
        self.playlist_name = playlist_name
        self.songs = songs or []

    @staticmethod
    def create_playlist(cursor, user_id: int, playlist_name: str) -> bool:
        """Create a new playlist for a user"""
        try:
            sql = """
            INSERT INTO playlists (user_id, playlist_name, songs)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (user_id, playlist_name, json.dumps([])))
            return True
        except Exception as e:
            print(f"Error creating playlist: {str(e)}")
            return False

    @staticmethod
    def add_song(cursor, user_id: int, playlist_name: str, song_info: Dict) -> bool:
        """Add a song to a playlist"""
        try:
            # First get current songs
            sql = "SELECT songs FROM playlists WHERE user_id = %s AND playlist_name = %s"
            cursor.execute(sql, (user_id, playlist_name))
            result = cursor.fetchone()
            
            if not result:
                return False
                
            current_songs = json.loads(result[0])
            if len(current_songs) >= 10:  # Max playlist size check
                return False
                
            current_songs.append(song_info)
            
            # Update playlist with new songs
            sql = """
            UPDATE playlists 
            SET songs = %s 
            WHERE user_id = %s AND playlist_name = %s
            """
            cursor.execute(sql, (json.dumps(current_songs), user_id, playlist_name))
            return True
        except Exception as e:
            print(f"Error adding song to playlist: {str(e)}")
            return False

class Admin:
    """Admin model for database operations"""
    def __init__(self, user_id: int, promoted_by: int, privileges: Dict = None):
        self.user_id = user_id
        self.promoted_by = promoted_by
        self.privileges = privileges or {"can_manage_vc": True, "can_manage_playlists": True}

    @staticmethod
    def promote_user(cursor, user_id: int, promoted_by: int, privileges: Dict = None) -> bool:
        """Promote a user to admin"""
        try:
            sql = """
            INSERT INTO admins (user_id, promoted_by, privileges)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (user_id, promoted_by, json.dumps(privileges or {"can_manage_vc": True, "can_manage_playlists": True})))
            return True
        except Exception as e:
            print(f"Error promoting user to admin: {str(e)}")
            return False

class Group:
    """Group model for database operations"""
    def __init__(self, group_id: int, group_name: str, added_by: int):
        self.group_id = group_id
        self.group_name = group_name
        self.added_by = added_by

    @staticmethod
    def add_group(cursor, group_id: int, group_name: str, added_by: int) -> bool:
        """Add a new group to the database"""
        try:
            sql = """
            INSERT INTO groups (group_id, group_name, added_by)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                group_name = VALUES(group_name),
                is_active = TRUE
            """
            cursor.execute(sql, (group_id, group_name, added_by))
            return True
        except Exception as e:
            print(f"Error adding group: {str(e)}")
            return False

    @staticmethod
    def update_member_count(cursor, group_id: int, count: int) -> bool:
        """Update group member count"""
        try:
            sql = "UPDATE groups SET member_count = %s WHERE group_id = %s"
            cursor.execute(sql, (count, group_id))
            return True
        except Exception as e:
            print(f"Error updating member count: {str(e)}")
            return False
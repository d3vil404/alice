from typing import Dict, List, Optional, Union
from ..database.db import db
from ..utils.helpers import format_duration
import json

class PlaylistManager:
    """Handles playlist operations for users"""
    
    @staticmethod
    async def create_playlist(user_id: int, playlist_name: str) -> Dict[str, Union[bool, str]]:
        """
        Create a new playlist for a user
        
        Args:
            user_id: Telegram user ID
            playlist_name: Name of the playlist
            
        Returns:
            dict: Status and message
        """
        try:
            with db.get_cursor() as cursor:
                # Check if user has reached maximum playlists (limit to 5 playlists per user)
                cursor.execute(
                    "SELECT COUNT(*) as count FROM playlists WHERE user_id = %s",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result and result['count'] >= 5:
                    return {
                        "success": False,
                        "message": "You have reached the maximum limit of 5 playlists"
                    }

                # Create new playlist
                cursor.execute(
                    "INSERT INTO playlists (user_id, playlist_name, songs) VALUES (%s, %s, %s)",
                    (user_id, playlist_name, json.dumps([]))
                )
                
                return {
                    "success": True,
                    "message": f"Playlist '{playlist_name}' created successfully"
                }

        except Exception as e:
            print(f"Error creating playlist: {str(e)}")
            return {
                "success": False,
                "message": "Error creating playlist. The playlist name might already exist."
            }

    @staticmethod
    async def add_to_playlist(
        user_id: int,
        playlist_name: str,
        song_info: Dict
    ) -> Dict[str, Union[bool, str]]:
        """
        Add a song to a playlist
        
        Args:
            user_id: Telegram user ID
            playlist_name: Name of the playlist
            song_info: Dictionary containing song information
            
        Returns:
            dict: Status and message
        """
        try:
            with db.get_cursor() as cursor:
                # Get current playlist
                cursor.execute(
                    "SELECT songs FROM playlists WHERE user_id = %s AND playlist_name = %s",
                    (user_id, playlist_name)
                )
                result = cursor.fetchone()
                
                if not result:
                    return {
                        "success": False,
                        "message": f"Playlist '{playlist_name}' not found"
                    }
                
                current_songs = json.loads(result['songs'])
                
                # Check playlist size limit
                if len(current_songs) >= 10:
                    return {
                        "success": False,
                        "message": "Playlist has reached the maximum limit of 10 songs"
                    }
                
                # Check if song already exists in playlist
                if any(song['url'] == song_info['url'] for song in current_songs):
                    return {
                        "success": False,
                        "message": "This song is already in the playlist"
                    }
                
                # Add new song
                current_songs.append({
                    "title": song_info['title'],
                    "url": song_info['url'],
                    "duration": song_info['duration'],
                    "added_at": song_info.get('added_at', None)
                })
                
                # Update playlist
                cursor.execute(
                    "UPDATE playlists SET songs = %s WHERE user_id = %s AND playlist_name = %s",
                    (json.dumps(current_songs), user_id, playlist_name)
                )
                
                return {
                    "success": True,
                    "message": f"Added '{song_info['title']}' to playlist '{playlist_name}'"
                }

        except Exception as e:
            print(f"Error adding song to playlist: {str(e)}")
            return {
                "success": False,
                "message": "Error adding song to playlist"
            }

    @staticmethod
    async def show_playlist(user_id: int, playlist_name: Optional[str] = None) -> Dict[str, Union[bool, str, List]]:
        """
        Show user's playlist(s)
        
        Args:
            user_id: Telegram user ID
            playlist_name: Optional specific playlist name
            
        Returns:
            dict: Status, message and playlist data
        """
        try:
            with db.get_cursor() as cursor:
                if playlist_name:
                    # Show specific playlist
                    cursor.execute(
                        "SELECT songs FROM playlists WHERE user_id = %s AND playlist_name = %s",
                        (user_id, playlist_name)
                    )
                    result = cursor.fetchone()
                    
                    if not result:
                        return {
                            "success": False,
                            "message": f"Playlist '{playlist_name}' not found",
                            "data": []
                        }
                    
                    songs = json.loads(result['songs'])
                    return {
                        "success": True,
                        "message": f"Playlist: {playlist_name}",
                        "data": songs
                    }
                else:
                    # Show all playlists
                    cursor.execute(
                        "SELECT playlist_name, songs FROM playlists WHERE user_id = %s",
                        (user_id,)
                    )
                    results = cursor.fetchall()
                    
                    if not results:
                        return {
                            "success": False,
                            "message": "No playlists found",
                            "data": []
                        }
                    
                    playlists = [{
                        "name": row['playlist_name'],
                        "songs": json.loads(row['songs'])
                    } for row in results]
                    
                    return {
                        "success": True,
                        "message": "Your playlists",
                        "data": playlists
                    }

        except Exception as e:
            print(f"Error showing playlist: {str(e)}")
            return {
                "success": False,
                "message": "Error retrieving playlist information",
                "data": []
            }

    @staticmethod
    async def modify_playlist(
        user_id: int,
        playlist_name: str,
        action: str,
        song_index: Optional[int] = None,
        new_order: Optional[List[int]] = None
    ) -> Dict[str, Union[bool, str]]:
        """
        Modify a playlist (remove song or reorder)
        
        Args:
            user_id: Telegram user ID
            playlist_name: Name of the playlist
            action: Action to perform ('remove' or 'reorder')
            song_index: Index of song to remove (for 'remove' action)
            new_order: New order of songs (for 'reorder' action)
            
        Returns:
            dict: Status and message
        """
        try:
            with db.get_cursor() as cursor:
                # Get current playlist
                cursor.execute(
                    "SELECT songs FROM playlists WHERE user_id = %s AND playlist_name = %s",
                    (user_id, playlist_name)
                )
                result = cursor.fetchone()
                
                if not result:
                    return {
                        "success": False,
                        "message": f"Playlist '{playlist_name}' not found"
                    }
                
                current_songs = json.loads(result['songs'])
                
                if action == "remove":
                    if song_index is None or song_index >= len(current_songs):
                        return {
                            "success": False,
                            "message": "Invalid song index"
                        }
                    
                    removed_song = current_songs.pop(song_index)
                    message = f"Removed '{removed_song['title']}' from playlist"
                    
                elif action == "reorder":
                    if not new_order or len(new_order) != len(current_songs):
                        return {
                            "success": False,
                            "message": "Invalid reorder sequence"
                        }
                    
                    # Create new ordered list
                    new_songs = [current_songs[i] for i in new_order]
                    current_songs = new_songs
                    message = "Playlist reordered successfully"
                    
                else:
                    return {
                        "success": False,
                        "message": "Invalid action"
                    }
                
                # Update playlist
                cursor.execute(
                    "UPDATE playlists SET songs = %s WHERE user_id = %s AND playlist_name = %s",
                    (json.dumps(current_songs), user_id, playlist_name)
                )
                
                return {
                    "success": True,
                    "message": message
                }

        except Exception as e:
            print(f"Error modifying playlist: {str(e)}")
            return {
                "success": False,
                "message": "Error modifying playlist"
            }

    @staticmethod
    async def delete_playlist(user_id: int, playlist_name: str) -> Dict[str, Union[bool, str]]:
        """
        Delete a playlist
        
        Args:
            user_id: Telegram user ID
            playlist_name: Name of the playlist to delete
            
        Returns:
            dict: Status and message
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "DELETE FROM playlists WHERE user_id = %s AND playlist_name = %s",
                    (user_id, playlist_name)
                )
                
                if cursor.rowcount > 0:
                    return {
                        "success": True,
                        "message": f"Playlist '{playlist_name}' deleted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Playlist '{playlist_name}' not found"
                    }

        except Exception as e:
            print(f"Error deleting playlist: {str(e)}")
            return {
                "success": False,
                "message": "Error deleting playlist"
            }

    @staticmethod
    async def get_playlist_songs(user_id: int, playlist_name: str) -> Optional[List[Dict]]:
        """
        Get songs from a playlist
        
        Args:
            user_id: Telegram user ID
            playlist_name: Name of the playlist
            
        Returns:
            Optional[List[Dict]]: List of songs or None if playlist not found
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT songs FROM playlists WHERE user_id = %s AND playlist_name = %s",
                    (user_id, playlist_name)
                )
                result = cursor.fetchone()
                
                if result:
                    return json.loads(result['songs'])
                return None

        except Exception as e:
            print(f"Error getting playlist songs: {str(e)}")
            return None

# Create global playlist manager instance
playlist_manager = PlaylistManager()
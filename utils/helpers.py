from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import math
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..database.db import db
from ..config import Config

async def is_admin(chat_id: int, user_id: int) -> bool:
    """
    Check if a user is an admin in the chat or bot admin
    
    Args:
        chat_id: Telegram chat ID
        user_id: User ID to check
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    try:
        # Check if user is bot owner
        if user_id == Config.OWNER_ID:
            return True

        # Check if user is bot admin
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM admins WHERE user_id = %s",
                (user_id,)
            )
            if cursor.fetchone():
                return True

        # Check if user is chat admin
        # This would typically use pyrogram's get_chat_member method
        # but for now we'll just check our database
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT g.* FROM groups g
                JOIN admins a ON g.group_id = %s
                WHERE a.user_id = %s
            """, (chat_id, user_id))
            return bool(cursor.fetchone())

    except Exception as e:
        print(f"Error checking admin status: {str(e)}")
        return False

def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to readable time
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if not seconds:
        return "00:00"
        
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def create_keyboard(buttons: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard from button data
    
    Args:
        buttons: List of button rows, each containing button data
        
    Returns:
        InlineKeyboardMarkup: Telegram inline keyboard
    """
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for button in row:
            keyboard_row.append(
                InlineKeyboardButton(
                    text=button['text'],
                    callback_data=button.get('callback_data'),
                    url=button.get('url')
                )
            )
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(keyboard)

def get_readable_time(seconds: int) -> str:
    """
    Convert seconds to human readable time
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Human readable time string
    """
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

def get_readable_size(size_in_bytes: int) -> str:
    """
    Convert bytes to human readable size
    
    Args:
        size_in_bytes: Size in bytes
        
    Returns:
        str: Human readable size string
    """
    if size_in_bytes is None:
        return "0B"
        
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f}{unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f}PB"

def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    Create a progress bar string
    
    Args:
        current: Current progress value
        total: Total value
        length: Length of progress bar
        
    Returns:
        str: Progress bar string
    """
    filled_length = int(length * current // total)
    return "▓" * filled_length + "░" * (length - filled_length)

def format_message_with_progress(
    title: str,
    current: int,
    total: int,
    speed: Optional[float] = None,
    eta: Optional[int] = None
) -> str:
    """
    Format a message with progress information
    
    Args:
        title: Title of the progress
        current: Current progress value
        total: Total value
        speed: Speed in bytes/second
        eta: Estimated time in seconds
        
    Returns:
        str: Formatted progress message
    """
    progress = min(100, round(current * 100 / total, 2))
    progress_bar = create_progress_bar(current, total)
    
    status = f"{title}\n"
    status += f"{progress_bar} {progress}%\n"
    status += f"Progress: {get_readable_size(current)} / {get_readable_size(total)}"
    
    if speed is not None:
        status += f"\nSpeed: {get_readable_size(speed)}/s"
    if eta is not None:
        status += f"\nETA: {get_readable_time(eta)}"
        
    return status

def create_playlist_keyboard(playlist_name: str, songs: List[Dict]) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for playlist management
    
    Args:
        playlist_name: Name of the playlist
        songs: List of songs in the playlist
        
    Returns:
        InlineKeyboardMarkup: Telegram inline keyboard
    """
    keyboard = []
    
    # Add song buttons
    for i, song in enumerate(songs):
        keyboard.append([
            InlineKeyboardButton(
                text=f"🎵 {song['title'][:30]}...",
                callback_data=f"play_song_{playlist_name}_{i}"
            )
        ])
    
    # Add control buttons
    controls = []
    if len(songs) > 0:
        controls.append(
            InlineKeyboardButton(
                text="🗑 Remove Song",
                callback_data=f"remove_song_{playlist_name}"
            )
        )
    if len(songs) < 10:
        controls.append(
            InlineKeyboardButton(
                text="➕ Add Song",
                callback_data=f"add_song_{playlist_name}"
            )
        )
    
    if controls:
        keyboard.append(controls)
    
    # Add playlist controls
    keyboard.append([
        InlineKeyboardButton(
            text="▶️ Play All",
            callback_data=f"play_playlist_{playlist_name}"
        ),
        InlineKeyboardButton(
            text="🗑 Delete Playlist",
            callback_data=f"delete_playlist_{playlist_name}"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)

def format_playlist_message(playlist_name: str, songs: List[Dict]) -> str:
    """
    Format a message showing playlist contents
    
    Args:
        playlist_name: Name of the playlist
        songs: List of songs in the playlist
        
    Returns:
        str: Formatted playlist message
    """
    message = f"📋 Playlist: {playlist_name}\n\n"
    
    if not songs:
        message += "No songs in playlist"
        return message
        
    for i, song in enumerate(songs, 1):
        duration = format_duration(song.get('duration', 0))
        message += f"{i}. {song['title']}\n"
        message += f"   ├ Duration: {duration}\n"
        message += f"   └ Added: {song.get('added_at', 'Unknown')}\n\n"
        
    message += f"\nTotal songs: {len(songs)}"
    return message

def validate_song_info(song_info: Dict) -> bool:
    """
    Validate song information
    
    Args:
        song_info: Dictionary containing song information
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ['title', 'url', 'duration']
    return all(field in song_info for field in required_fields)

def get_chat_title(chat_id: int) -> Optional[str]:
    """
    Get chat title from database
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        Optional[str]: Chat title if found, None otherwise
    """
    try:
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT group_name FROM groups WHERE group_id = %s",
                (chat_id,)
            )
            result = cursor.fetchone()
            return result['group_name'] if result else None
    except Exception as e:
        print(f"Error getting chat title: {str(e)}")
        return None

def update_user_activity(user_id: int):
    """
    Update user's last active timestamp
    
    Args:
        user_id: Telegram user ID
    """
    try:
        with db.get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET last_active = NOW() WHERE user_id = %s",
                (user_id,)
            )
    except Exception as e:
        print(f"Error updating user activity: {str(e)}")
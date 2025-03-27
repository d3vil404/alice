import asyncio
from typing import Optional, Dict, Union
from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pytgcalls.types.input_stream import InputAudioStream, InputVideoStream
from pytgcalls.exceptions import NoActiveGroupCall, GroupCallNotFound

from ..config import Config
from ..database.db import db
from ..utils.fetcher import YouTubeDL
from ..utils.helpers import format_duration

class MusicPlayer:
    """Handles music playback in Telegram video chats"""
    
    def __init__(self):
        # Initialize the assistant client
        self.assistant = Client(
            "AliceMusicAssistant",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.ASSISTANT_TOKEN
        )
        
        # Initialize PyTgCalls
        self.call_py = PyTgCalls(self.assistant)
        
        # Active calls dictionary {chat_id: {current_song: dict, playlist: list}}
        self.active_calls = {}
        
        # YouTube downloader
        self.ytdl = YouTubeDL()

    async def start(self):
        """Start the assistant client and PyTgCalls"""
        await self.assistant.start()
        await self.call_py.start()
        print("Music Player initialized successfully")

    async def stop(self):
        """Stop the assistant client and PyTgCalls"""
        await self.call_py.stop()
        await self.assistant.stop()

    async def join_group_call(self, chat_id: int) -> bool:
        """
        Join the group call in specified chat
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            bool: True if joined successfully, False otherwise
        """
        try:
            await self.call_py.join_group_call(
                chat_id,
                InputAudioStream(
                    'silence.mp3',  # Initial silent stream
                    video_flags=InputVideoStream(
                        'black.mp4'  # Initial black screen
                    )
                )
            )
            return True
        except (NoActiveGroupCall, GroupCallNotFound):
            return False
        except Exception as e:
            print(f"Error joining group call: {str(e)}")
            return False

    async def leave_group_call(self, chat_id: int):
        """Leave the group call in specified chat"""
        try:
            await self.call_py.leave_group_call(chat_id)
            if chat_id in self.active_calls:
                del self.active_calls[chat_id]
        except Exception as e:
            print(f"Error leaving group call: {str(e)}")

    async def play_song(self, chat_id: int, user_id: int, query: str) -> Dict[str, Union[bool, str]]:
        """
        Play a song in the group call
        
        Args:
            chat_id: Telegram chat ID
            user_id: User ID who requested the song
            query: Song name or URL
            
        Returns:
            dict: Status and message
        """
        try:
            # Fetch song info and stream URL
            song_info = await self.ytdl.extract_info(query)
            if not song_info:
                return {"success": False, "message": "Could not find the song"}

            # Join call if not already in
            if chat_id not in self.active_calls:
                if not await self.join_group_call(chat_id):
                    return {"success": False, "message": "No active group call found"}
                self.active_calls[chat_id] = {"current_song": None, "playlist": []}

            # Add song to playlist or play immediately
            if self.active_calls[chat_id]["current_song"]:
                # Add to playlist if something is playing
                if len(self.active_calls[chat_id]["playlist"]) >= 10:
                    return {"success": False, "message": "Playlist is full (max 10 songs)"}
                    
                self.active_calls[chat_id]["playlist"].append({
                    "title": song_info["title"],
                    "duration": song_info["duration"],
                    "url": song_info["url"],
                    "requested_by": user_id
                })
                
                return {
                    "success": True,
                    "message": f"Added to playlist: {song_info['title']}"
                }
            else:
                # Play immediately if nothing is playing
                await self._stream_song(chat_id, song_info, user_id)
                return {
                    "success": True,
                    "message": f"Now playing: {song_info['title']}"
                }

        except Exception as e:
            print(f"Error playing song: {str(e)}")
            return {"success": False, "message": "Error playing song"}

    async def _stream_song(self, chat_id: int, song_info: dict, user_id: int):
        """Internal method to stream a song"""
        try:
            await self.call_py.change_stream(
                chat_id,
                InputAudioStream(
                    song_info["url"],
                    video_flags=InputVideoStream(
                        song_info.get("video_url", "black.mp4")
                    )
                )
            )
            
            self.active_calls[chat_id]["current_song"] = {
                "title": song_info["title"],
                "duration": song_info["duration"],
                "url": song_info["url"],
                "requested_by": user_id
            }
            
            # Update database
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO active_streams (group_id, current_song, requested_by)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        current_song = VALUES(current_song),
                        requested_by = VALUES(requested_by)
                """, (chat_id, song_info["title"], user_id))

        except Exception as e:
            print(f"Error streaming song: {str(e)}")
            await self.skip_song(chat_id)

    async def stop_playback(self, chat_id: int) -> Dict[str, Union[bool, str]]:
        """
        Stop current playback and clear playlist
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            dict: Status and message
        """
        try:
            await self.leave_group_call(chat_id)
            return {"success": True, "message": "Playback stopped and playlist cleared"}
        except Exception as e:
            print(f"Error stopping playback: {str(e)}")
            return {"success": False, "message": "Error stopping playback"}

    async def skip_song(self, chat_id: int) -> Dict[str, Union[bool, str]]:
        """
        Skip current song and play next in playlist
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            dict: Status and message
        """
        try:
            if chat_id not in self.active_calls:
                return {"success": False, "message": "No active playback"}

            if not self.active_calls[chat_id]["playlist"]:
                await self.stop_playback(chat_id)
                return {"success": True, "message": "No more songs in playlist"}

            # Get next song from playlist
            next_song = self.active_calls[chat_id]["playlist"].pop(0)
            await self._stream_song(
                chat_id,
                {
                    "title": next_song["title"],
                    "url": next_song["url"],
                    "duration": next_song["duration"]
                },
                next_song["requested_by"]
            )
            
            return {
                "success": True,
                "message": f"Skipped to next song: {next_song['title']}"
            }

        except Exception as e:
            print(f"Error skipping song: {str(e)}")
            return {"success": False, "message": "Error skipping song"}

    async def get_active_calls(self) -> Dict[int, Dict]:
        """Get all active calls and their current songs"""
        return self.active_calls

    # PyTgCalls event handlers
    async def on_stream_end(self, client: PyTgCalls, update: Update):
        """Handle stream end event"""
        chat_id = update.chat_id
        await self.skip_song(chat_id)

# Create global player instance
player = MusicPlayer()
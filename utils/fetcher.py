import yt_dlp
import asyncio
from typing import Dict, Optional, Union
import re
from datetime import datetime

class YouTubeDL:
    """YouTube downloader and metadata extractor"""
    
    def __init__(self):
        """Initialize with optimal configurations"""
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_color': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        # Regex patterns
        self.youtube_regex = (
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.'
            r'(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )

    def is_youtube_url(self, url: str) -> bool:
        """
        Check if the given URL is a valid YouTube URL
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if valid YouTube URL, False otherwise
        """
        return bool(re.match(self.youtube_regex, url))

    async def extract_info(self, query: str) -> Optional[Dict[str, Union[str, int]]]:
        """
        Extract information from YouTube video/song
        
        Args:
            query: YouTube URL or search query
            
        Returns:
            Optional[Dict]: Song information or None if extraction fails
        """
        try:
            # If not a YouTube URL, search for it
            if not self.is_youtube_url(query):
                search_opts = self.ydl_opts.copy()
                search_opts['default_search'] = 'ytsearch'
                query = f"ytsearch:{query}"

            # Run youtube-dl in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))

            # If it's a playlist or search result, get the first item
            if 'entries' in info:
                info = info['entries'][0]

            # Extract relevant information
            return {
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration', 0),
                'url': info.get('url', None),
                'thumbnail': info.get('thumbnail', None),
                'webpage_url': info.get('webpage_url', None),
                'uploader': info.get('uploader', 'Unknown Artist'),
                'view_count': info.get('view_count', 0),
                'added_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error extracting info: {str(e)}")
            return None

    async def get_video_stream(self, url: str) -> Optional[Dict[str, str]]:
        """
        Get video stream URL for video chat playback
        
        Args:
            url: YouTube URL
            
        Returns:
            Optional[Dict]: Stream URLs for audio and video
        """
        try:
            video_opts = self.ydl_opts.copy()
            video_opts['format'] = 'best'  # Get best quality for video
            
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                
            return {
                'audio_url': info.get('url'),
                'video_url': info.get('url')
            }

        except Exception as e:
            print(f"Error getting video stream: {str(e)}")
            return None

    async def search_songs(self, query: str, limit: int = 5) -> list:
        """
        Search for songs on YouTube
        
        Args:
            query: Search query
            limit: Maximum number of results (default: 5)
            
        Returns:
            list: List of song information dictionaries
        """
        try:
            search_opts = self.ydl_opts.copy()
            search_opts['default_search'] = 'ytsearch'
            search_query = f"ytsearch{limit}:{query}"
            
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
                
            results = []
            for entry in info['entries']:
                if entry:
                    results.append({
                        'title': entry.get('title', 'Unknown Title'),
                        'duration': entry.get('duration', 0),
                        'url': entry.get('webpage_url', None),
                        'thumbnail': entry.get('thumbnail', None),
                        'uploader': entry.get('uploader', 'Unknown Artist'),
                        'view_count': entry.get('view_count', 0)
                    })
            
            return results

        except Exception as e:
            print(f"Error searching songs: {str(e)}")
            return []

    def format_duration(self, duration: int) -> str:
        """
        Format duration in seconds to HH:MM:SS
        
        Args:
            duration: Duration in seconds
            
        Returns:
            str: Formatted duration string
        """
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

# Create global YouTube downloader instance
youtube = YouTubeDL()
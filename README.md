# Alice Music Bot

A Telegram bot that plays music and videos in group voice chats using a separate assistant account.

## Features

- Play music/videos in Telegram group voice chats
- Playlist management (create, modify, delete)
- Admin controls
- System monitoring
- MySQL database integration
- Protected configuration

## Commands

- `/play <song name | URL>` - Play song in VC
- `/stop` - Stop current playback (Admins only)
- `/skip` - Skip to next song (Admins only)
- `/video <URL>` - Play video in VC
- `/createplaylist <name>` - Create new playlist
- `/showplaylist` - Show your playlists
- `/delplaylist` - Delete playlist
- `/playlist` - Play entire playlist
- `/activegc` - Show active groups
- `/sysinfo` - Show system info
- `/promo @username` - Promote admin
- `/allgclist` - List all groups
- `/allusers` - List all users

## Prerequisites

- Python 3.8 or higher
- MySQL Server
- FFmpeg

## Setup Instructions

1. Get Required Credentials:
   
   a) Telegram API Credentials (from my.telegram.org):
      - API_ID
      - API_HASH
   
   b) Bot Token (from @BotFather):
      - Create new bot
      - Copy bot token
   
   c) Assistant Account:
      - Generate string session:
        ```bash
        pip install pyrogram tgcrypto
        python3 -c "from pyrogram import Client; Client('assistant', api_id=YOUR_API_ID, api_hash='YOUR_API_HASH').run()"
        ```
      - Copy session string

2. Configure Bot:
   
   Edit `.env` file:
   ```env
   # Bot Configuration
   BOT_TOKEN=your_bot_token_here
   ASSISTANT_TOKEN=your_assistant_token_here
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here
   OWNER_ID=your_telegram_id_here

   # Database Configuration
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=your_mysql_username
   DB_PASSWORD=your_mysql_password
   DB_NAME=alice_music_bot
   ```

3. Install & Run:
   ```bash
   cd AliceMusicBot
   chmod +x start.sh
   ./start.sh
   ```

## Project Structure

```
AliceMusicBot/
│── config.py               # Configuration handler
│── main.py                # Main bot code
│── database/
│   ├── db.py              # Database connection
│   ├── models.py          # Database models
│── modules/
│   ├── player.py          # Music player
│   ├── playlist.py        # Playlist manager
│   ├── admin.py           # Admin controls
│── handlers/
│   ├── commands.py        # Command handlers
│── utils/
│   ├── fetcher.py         # YouTube fetcher
│   ├── helpers.py         # Helper functions
```

## Support

- Developer: Rishi Shakya
- Contact: +91 9457874080
- Website: Codelinex.com

## License

This project is protected and requires permission for use.
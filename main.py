import asyncio
from pyrogram import Client, idle
from pyrogram.types import BotCommand

from config import Config
from database.db import init_db
from modules.player import player
from handlers.commands import register_handlers

class AliceMusicBot:
    """Main bot class"""
    
    def __init__(self):
        """Initialize bot instance"""
        # Initialize Telegram client
        self.app = Client(
            "AliceMusicBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        
        # Set bot commands
        self.commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("play", "Play a song in VC"),
            BotCommand("stop", "Stop current playback"),
            BotCommand("skip", "Skip to next song"),
            BotCommand("video", "Play a video in VC"),
            BotCommand("createplaylist", "Create a new playlist"),
            BotCommand("showplaylist", "Show your playlists"),
            BotCommand("delplaylist", "Delete a playlist"),
            BotCommand("playlist", "Play your playlist"),
            BotCommand("activegc", "Show active groups"),
            BotCommand("sysinfo", "Show system info"),
            BotCommand("promo", "Promote a user as admin"),
            BotCommand("allgclist", "List all groups"),
            BotCommand("allusers", "List all users")
        ]

    async def start(self):
        """Start the bot"""
        try:
            # Initialize database
            if not init_db():
                print("Failed to initialize database")
                return False

            # Start Telegram client
            await self.app.start()
            print("Bot client started successfully")

            # Set bot commands
            await self.app.set_bot_commands(self.commands)
            
            # Initialize music player
            await player.start()
            print("Music player initialized successfully")
            
            # Register command handlers
            register_handlers(self.app)
            print("Command handlers registered successfully")
            
            # Update bot profile
            await self.app.set_bot_description(
                "Alice Music Bot - Your personal music assistant for Telegram voice chats. "
                "Play music, manage playlists, and enjoy high-quality audio with friends!"
            )
            
            print(
                f"Bot started successfully!\n"
                f"Username: @{(await self.app.get_me()).username}"
            )
            
            # Idle the bot
            await idle()
            
        except Exception as e:
            print(f"Error starting bot: {str(e)}")
            return False
        
        finally:
            # Stop the bot
            await self.stop()

    async def stop(self):
        """Stop the bot"""
        try:
            # Stop music player
            await player.stop()
            
            # Stop Telegram client
            await self.app.stop()
            
        except Exception as e:
            print(f"Error stopping bot: {str(e)}")

    @staticmethod
    def run():
        """Run the bot"""
        # Verify config integrity
        if not Config.verify_file_integrity():
            print("Config file integrity check failed")
            return
            
        try:
            Config.validate_config()
        except ValueError as e:
            print(f"Configuration error: {str(e)}")
            return
            
        # Create and run bot instance
        bot = AliceMusicBot()
        asyncio.run(bot.start())

if __name__ == "__main__":
    AliceMusicBot.run()
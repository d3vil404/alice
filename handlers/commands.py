from typing import Dict, Union
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChatAdminRequired, UserNotParticipant

from ..config import Config
from ..modules.player import player
from ..modules.playlist import playlist_manager
from ..modules.admin import admin_manager
from ..utils.helpers import (
    is_admin,
    format_duration,
    create_keyboard,
    get_readable_time,
    get_readable_size
)
from ..database.db import db

# Command handlers
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    try:
        # Create user in database if not exists
        with db.get_cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO users (user_id, username, first_name, last_name) VALUES (%s, %s, %s, %s)",
                (message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
            )

        # Create welcome message with inline keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📚 Commands", callback_data="show_commands"),
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ],
            [
                InlineKeyboardButton("🎵 Play Music", callback_data="play_music"),
                InlineKeyboardButton("📋 Playlist", callback_data="manage_playlist")
            ]
        ])

        await message.reply_text(
            f"👋 Hello {message.from_user.first_name}!\n\n"
            "I'm Alice Music Bot, your personal music assistant. I can play music in "
            "voice chats and help you manage your playlists.\n\n"
            "Click the buttons below to get started!",
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"Error in start command: {str(e)}")
        await message.reply_text("An error occurred. Please try again later.")

async def play_command(client: Client, message: Message):
    """Handle /play command"""
    try:
        # Check if user is in a voice chat
        if not message.chat.type in ["group", "supergroup"]:
            await message.reply_text("This command can only be used in groups!")
            return

        # Extract song query
        if len(message.command) < 2:
            await message.reply_text("Please provide a song name or URL!")
            return

        query = " ".join(message.command[1:])

        # Play the song
        result = await player.play_song(
            message.chat.id,
            message.from_user.id,
            query
        )

        if result["success"]:
            await message.reply_text(result["message"])
        else:
            await message.reply_text(f"❌ Error: {result['message']}")

    except Exception as e:
        print(f"Error in play command: {str(e)}")
        await message.reply_text("An error occurred while trying to play the song.")

async def stop_command(client: Client, message: Message):
    """Handle /stop command"""
    try:
        # Check if user is admin
        if not await is_admin(message.chat.id, message.from_user.id):
            await message.reply_text("⚠️ Only admins can use this command!")
            return

        result = await player.stop_playback(message.chat.id)
        await message.reply_text(result["message"])

    except Exception as e:
        print(f"Error in stop command: {str(e)}")
        await message.reply_text("An error occurred while trying to stop the playback.")

async def skip_command(client: Client, message: Message):
    """Handle /skip command"""
    try:
        # Check if user is admin
        if not await is_admin(message.chat.id, message.from_user.id):
            await message.reply_text("⚠️ Only admins can use this command!")
            return

        result = await player.skip_song(message.chat.id)
        await message.reply_text(result["message"])

    except Exception as e:
        print(f"Error in skip command: {str(e)}")
        await message.reply_text("An error occurred while trying to skip the song.")

async def playlist_command(client: Client, message: Message):
    """Handle playlist related commands"""
    try:
        command_parts = message.command
        if len(command_parts) < 2:
            # Show user's playlists
            result = await playlist_manager.show_playlist(message.from_user.id)
            if result["success"]:
                text = "Your Playlists:\n\n"
                for playlist in result["data"]:
                    text += f"📋 {playlist['name']} ({len(playlist['songs'])} songs)\n"
                await message.reply_text(text)
            else:
                await message.reply_text(result["message"])
            return

        action = command_parts[1].lower()
        
        if action == "create":
            if len(command_parts) < 3:
                await message.reply_text("Please provide a playlist name!")
                return
            playlist_name = " ".join(command_parts[2:])
            result = await playlist_manager.create_playlist(message.from_user.id, playlist_name)
            
        elif action == "add":
            if len(command_parts) < 4:
                await message.reply_text("Please provide playlist name and song!")
                return
            playlist_name = command_parts[2]
            song_query = " ".join(command_parts[3:])
            # First get song info
            song_info = await player.ytdl.extract_info(song_query)
            if song_info:
                result = await playlist_manager.add_to_playlist(
                    message.from_user.id,
                    playlist_name,
                    song_info
                )
            else:
                result = {"success": False, "message": "Could not find the song"}
            
        elif action == "delete":
            if len(command_parts) < 3:
                await message.reply_text("Please provide the playlist name to delete!")
                return
            playlist_name = " ".join(command_parts[2:])
            result = await playlist_manager.delete_playlist(message.from_user.id, playlist_name)
            
        else:
            result = {
                "success": False,
                "message": "Invalid playlist command! Use create/add/delete."
            }

        await message.reply_text(result["message"])

    except Exception as e:
        print(f"Error in playlist command: {str(e)}")
        await message.reply_text("An error occurred while managing the playlist.")

async def sysinfo_command(client: Client, message: Message):
    """Handle /sysinfo command"""
    try:
        # Check if user is admin
        if not await is_admin(message.chat.id, message.from_user.id):
            await message.reply_text("⚠️ Only admins can use this command!")
            return

        result = await admin_manager.get_system_info()
        if result["success"]:
            info = result["data"]
            text = "📊 System Information\n\n"
            
            # System info
            text += "🖥 System:\n"
            text += f"• Platform: {info['system']['platform']}\n"
            text += f"• Release: {info['system']['release']}\n"
            text += f"• Python: {info['system']['python_version']}\n\n"
            
            # CPU info
            text += "💻 CPU:\n"
            text += f"• Usage: {info['cpu']['usage_percent']}%\n"
            text += f"• Cores: {info['cpu']['cores']}\n\n"
            
            # Memory info
            text += "🧠 Memory:\n"
            text += f"• Total: {info['memory']['total']}\n"
            text += f"• Used: {info['memory']['used']}\n"
            text += f"• Usage: {info['memory']['percent']}%\n\n"
            
            # Disk info
            text += "💾 Disk:\n"
            text += f"• Total: {info['disk']['total']}\n"
            text += f"• Used: {info['disk']['used']}\n"
            text += f"• Usage: {info['disk']['percent']}%\n\n"
            
            # Bot info
            text += "🤖 Bot:\n"
            text += f"• Uptime: {info['bot']['uptime']}\n"
            text += f"• Started: {info['bot']['start_time']}"
            
            await message.reply_text(text)
        else:
            await message.reply_text(f"❌ Error: {result['message']}")

    except Exception as e:
        print(f"Error in sysinfo command: {str(e)}")
        await message.reply_text("An error occurred while getting system information.")

async def promo_command(client: Client, message: Message):
    """Handle /promo command"""
    try:
        # Check if user is owner or admin
        if message.from_user.id != Config.OWNER_ID and not await is_admin(message.chat.id, message.from_user.id):
            await message.reply_text("⚠️ Only the owner and admins can use this command!")
            return

        if len(message.command) != 2:
            await message.reply_text("Please provide the username to promote!")
            return

        username = message.command[1].replace("@", "")
        
        # Get user ID from username
        try:
            user = await client.get_users(username)
            result = await admin_manager.promote_user(
                user.id,
                message.from_user.id,
                username
            )
            await message.reply_text(result["message"])
        except Exception as e:
            await message.reply_text(f"Could not find user with username @{username}")

    except Exception as e:
        print(f"Error in promo command: {str(e)}")
        await message.reply_text("An error occurred while promoting the user.")

async def activegc_command(client: Client, message: Message):
    """Handle /activegc command"""
    try:
        # Check if user is admin
        if not await is_admin(message.chat.id, message.from_user.id):
            await message.reply_text("⚠️ Only admins can use this command!")
            return

        result = await admin_manager.get_active_groups()
        if result["success"]:
            if not result["data"]:
                await message.reply_text("No active groups found.")
                return

            text = "📊 Active Groups:\n\n"
            for group in result["data"]:
                text += f"• {group['name']}\n"
                text += f"  └ Members: {group['member_count']}\n"
                text += f"  └ Active Streams: {group['active_streams']}\n"
                text += f"  └ Last Active: {group['last_active']}\n\n"

            await message.reply_text(text)
        else:
            await message.reply_text(f"❌ Error: {result['message']}")

    except Exception as e:
        print(f"Error in activegc command: {str(e)}")
        await message.reply_text("An error occurred while getting active groups.")

async def allgclist_command(client: Client, message: Message):
    """Handle /allgclist command"""
    try:
        # Check if user is admin
        if not await is_admin(message.chat.id, message.from_user.id):
            await message.reply_text("⚠️ Only admins can use this command!")
            return

        result = await admin_manager.get_all_groups()
        if result["success"]:
            if not result["data"]:
                await message.reply_text("No groups found.")
                return

            text = "📋 All Groups:\n\n"
            for group in result["data"]:
                text += f"• {group['name']}\n"
                text += f"  └ Members: {group['member_count']}\n"
                text += f"  └ Status: {'🟢 Active' if group['is_active'] else '🔴 Inactive'}\n"
                text += f"  └ Added by: @{group['added_by']}\n"
                text += f"  └ Added on: {group['created_at']}\n\n"

            await message.reply_text(text)
        else:
            await message.reply_text(f"❌ Error: {result['message']}")

    except Exception as e:
        print(f"Error in allgclist command: {str(e)}")
        await message.reply_text("An error occurred while getting group list.")

async def allusers_command(client: Client, message: Message):
    """Handle /allusers command"""
    try:
        # Check if user is admin
        if not await is_admin(message.chat.id, message.from_user.id):
            await message.reply_text("⚠️ Only admins can use this command!")
            return

        result = await admin_manager.get_all_users()
        if result["success"]:
            if not result["data"]:
                await message.reply_text("No users found.")
                return

            text = "👥 All Users:\n\n"
            for user in result["data"]:
                name = f"{user['first_name']} {user['last_name']}" if user['last_name'] else user['first_name']
                text += f"• {name} (@{user['username']})\n"
                text += f"  └ Status: {'👑 Admin' if user['is_admin'] else '👤 User'}\n"
                text += f"  └ Playlists: {user['playlist_count']}\n"
                text += f"  └ Last Active: {user['last_active']}\n\n"

            await message.reply_text(text)
        else:
            await message.reply_text(f"❌ Error: {result['message']}")

    except Exception as e:
        print(f"Error in allusers command: {str(e)}")
        await message.reply_text("An error occurred while getting user list.")

# Register all command handlers
def register_handlers(app: Client):
    """Register all command handlers"""
    app.add_handler(filters.command("start"), start_command)
    app.add_handler(filters.command("play"), play_command)
    app.add_handler(filters.command("stop"), stop_command)
    app.add_handler(filters.command("skip"), skip_command)
    app.add_handler(filters.command(["playlist", "createplaylist", "showplaylist", "delplaylist"]), playlist_command)
    app.add_handler(filters.command("sysinfo"), sysinfo_command)
    app.add_handler(filters.command("promo"), promo_command)
    app.add_handler(filters.command("activegc"), activegc_command)
    app.add_handler(filters.command("allgclist"), allgclist_command)
    app.add_handler(filters.command("allusers"), allusers_command)
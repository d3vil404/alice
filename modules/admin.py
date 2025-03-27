import psutil
import platform
from datetime import datetime
from typing import Dict, List, Union, Optional
import json

from ..database.db import db
from ..config import Config

class AdminManager:
    """Handles administrative operations and system monitoring"""
    
    def __init__(self):
        self.start_time = datetime.now()

    async def promote_user(self, user_id: int, promoted_by: int, username: str) -> Dict[str, Union[bool, str]]:
        """
        Promote a user to admin status
        
        Args:
            user_id: Telegram user ID to promote
            promoted_by: Telegram user ID of the promoter
            username: Username of the user being promoted
            
        Returns:
            dict: Status and message
        """
        try:
            # Check if promoter is owner or admin
            if promoted_by != Config.OWNER_ID:
                with db.get_cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM admins WHERE user_id = %s",
                        (promoted_by,)
                    )
                    if not cursor.fetchone():
                        return {
                            "success": False,
                            "message": "Only the owner and admins can promote users"
                        }

            # Check if user is already an admin
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM admins WHERE user_id = %s",
                    (user_id,)
                )
                if cursor.fetchone():
                    return {
                        "success": False,
                        "message": f"User {username} is already an admin"
                    }

                # Add user to admins table
                default_privileges = {
                    "can_manage_vc": True,
                    "can_manage_playlists": True,
                    "can_view_stats": True
                }
                
                cursor.execute(
                    "INSERT INTO admins (user_id, promoted_by, privileges) VALUES (%s, %s, %s)",
                    (user_id, promoted_by, json.dumps(default_privileges))
                )
                
                return {
                    "success": True,
                    "message": f"Successfully promoted {username} to admin"
                }

        except Exception as e:
            print(f"Error promoting user: {str(e)}")
            return {
                "success": False,
                "message": "Error occurred while promoting user"
            }

    async def get_system_info(self) -> Dict[str, Union[bool, str, Dict]]:
        """
        Get system information including CPU, RAM, and uptime
        
        Returns:
            dict: Status, message and system information
        """
        try:
            # Calculate uptime
            uptime = datetime.now() - self.start_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds

            # Get CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Get memory information
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024 * 1024 * 1024)  # Convert to GB
            memory_used = memory.used / (1024 * 1024 * 1024)
            memory_percent = memory.percent

            # Get disk information
            disk = psutil.disk_usage('/')
            disk_total = disk.total / (1024 * 1024 * 1024)
            disk_used = disk.used / (1024 * 1024 * 1024)
            disk_percent = disk.percent

            system_info = {
                "system": {
                    "platform": platform.system(),
                    "release": platform.release(),
                    "python_version": platform.python_version()
                },
                "cpu": {
                    "usage_percent": cpu_percent,
                    "cores": cpu_count
                },
                "memory": {
                    "total": f"{memory_total:.2f} GB",
                    "used": f"{memory_used:.2f} GB",
                    "percent": memory_percent
                },
                "disk": {
                    "total": f"{disk_total:.2f} GB",
                    "used": f"{disk_used:.2f} GB",
                    "percent": disk_percent
                },
                "bot": {
                    "uptime": uptime_str,
                    "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }

            return {
                "success": True,
                "message": "System information retrieved successfully",
                "data": system_info
            }

        except Exception as e:
            print(f"Error getting system info: {str(e)}")
            return {
                "success": False,
                "message": "Error retrieving system information",
                "data": {}
            }

    async def get_active_groups(self) -> Dict[str, Union[bool, str, List]]:
        """
        Get list of active groups where the bot is being used
        
        Returns:
            dict: Status, message and list of active groups
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT g.*, COUNT(DISTINCT a.stream_id) as active_streams
                    FROM groups g
                    LEFT JOIN active_streams a ON g.group_id = a.group_id
                    WHERE g.is_active = TRUE
                    GROUP BY g.group_id
                    ORDER BY g.last_active DESC
                """)
                groups = cursor.fetchall()

                if not groups:
                    return {
                        "success": False,
                        "message": "No active groups found",
                        "data": []
                    }

                active_groups = [{
                    "group_id": group['group_id'],
                    "name": group['group_name'],
                    "member_count": group['member_count'],
                    "active_streams": group['active_streams'],
                    "last_active": group['last_active'].strftime("%Y-%m-%d %H:%M:%S")
                } for group in groups]

                return {
                    "success": True,
                    "message": f"Found {len(active_groups)} active groups",
                    "data": active_groups
                }

        except Exception as e:
            print(f"Error getting active groups: {str(e)}")
            return {
                "success": False,
                "message": "Error retrieving active groups",
                "data": []
            }

    async def get_all_groups(self) -> Dict[str, Union[bool, str, List]]:
        """
        Get list of all groups where the bot is added
        
        Returns:
            dict: Status, message and list of all groups
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT g.*, u.username as added_by_username
                    FROM groups g
                    LEFT JOIN users u ON g.added_by = u.user_id
                    ORDER BY g.created_at DESC
                """)
                groups = cursor.fetchall()

                if not groups:
                    return {
                        "success": False,
                        "message": "No groups found",
                        "data": []
                    }

                all_groups = [{
                    "group_id": group['group_id'],
                    "name": group['group_name'],
                    "member_count": group['member_count'],
                    "is_active": group['is_active'],
                    "added_by": group['added_by_username'],
                    "created_at": group['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                } for group in groups]

                return {
                    "success": True,
                    "message": f"Found {len(all_groups)} groups",
                    "data": all_groups
                }

        except Exception as e:
            print(f"Error getting all groups: {str(e)}")
            return {
                "success": False,
                "message": "Error retrieving groups",
                "data": []
            }

    async def get_all_users(self) -> Dict[str, Union[bool, str, List]]:
        """
        Get list of all users using the bot
        
        Returns:
            dict: Status, message and list of all users
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.*, 
                           COUNT(DISTINCT p.playlist_id) as playlist_count,
                           COUNT(DISTINCT a.admin_id) as is_admin
                    FROM users u
                    LEFT JOIN playlists p ON u.user_id = p.user_id
                    LEFT JOIN admins a ON u.user_id = a.user_id
                    GROUP BY u.user_id
                    ORDER BY u.last_active DESC
                """)
                users = cursor.fetchall()

                if not users:
                    return {
                        "success": False,
                        "message": "No users found",
                        "data": []
                    }

                all_users = [{
                    "user_id": user['user_id'],
                    "username": user['username'],
                    "first_name": user['first_name'],
                    "last_name": user['last_name'],
                    "is_admin": bool(user['is_admin']),
                    "playlist_count": user['playlist_count'],
                    "last_active": user['last_active'].strftime("%Y-%m-%d %H:%M:%S")
                } for user in users]

                return {
                    "success": True,
                    "message": f"Found {len(all_users)} users",
                    "data": all_users
                }

        except Exception as e:
            print(f"Error getting all users: {str(e)}")
            return {
                "success": False,
                "message": "Error retrieving users",
                "data": []
            }

# Create global admin manager instance
admin_manager = AdminManager()
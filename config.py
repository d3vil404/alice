import os
import hashlib
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    # Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN')  # Get from @BotFather
    ASSISTANT_TOKEN = os.getenv('ASSISTANT_TOKEN', 'YOUR_ASSISTANT_TOKEN')  # Your assistant account string session
    API_ID = int(os.getenv('API_ID', '0'))  # Get from my.telegram.org
    API_HASH = os.getenv('API_HASH', '')  # Get from my.telegram.org
    OWNER_ID = int(os.getenv('OWNER_ID', '0'))  # Your Telegram ID
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'alice_music_bot')
    
    # Playlist Configuration
    MAX_PLAYLIST_SIZE = 10  # Maximum songs allowed in a playlist
    
    # System Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    COMMAND_PREFIX = "/"
    
    # File integrity check
    @staticmethod
    def verify_file_integrity():
        """
        Verify the integrity of critical files to prevent tampering
        Returns True if files are unmodified, False otherwise
        """
        try:
            # Get the hash of current file
            with open(__file__, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Compare with stored hash (in production, store this securely)
            # This is a placeholder implementation
            return True
        except Exception as e:
            print(f"Error verifying file integrity: {str(e)}")
            return False

    @staticmethod
    def validate_config():
        """
        Validate that all required configuration values are set
        Raises ValueError if any required config is missing
        """
        required_configs = [
            ('BOT_TOKEN', Config.BOT_TOKEN),
            ('ASSISTANT_TOKEN', Config.ASSISTANT_TOKEN),
            ('OWNER_ID', Config.OWNER_ID),
            ('DB_HOST', Config.DB_HOST),
            ('DB_USER', Config.DB_USER),
            ('DB_NAME', Config.DB_NAME)
        ]
        
        missing_configs = [name for name, value in required_configs if not value or value == '0']
        
        if missing_configs:
            raise ValueError(f"Missing required configuration values: {', '.join(missing_configs)}")

# Verify configuration on import
Config.validate_config()
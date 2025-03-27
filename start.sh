#!/bin/bash

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade pip
python3 -m pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "Installing required packages..."
    pip install pyrogram tgcrypto python-dotenv yt-dlp pytgcalls mysql-connector-python psutil
    
    # Save requirements
    pip freeze > requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Bot Configuration
BOT_TOKEN=your_bot_token_here
ASSISTANT_TOKEN=your_assistant_token_here
API_ID=your_api_id_here
API_HASH=your_api_hash_here
OWNER_ID=your_telegram_id_here

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=alice_music_bot

# Logging Configuration
LOG_LEVEL=INFO
EOL
    echo "Please edit .env file with your configuration values"
    exit 1
fi

# Start the bot
echo "Starting Alice Music Bot..."
python3 main.py
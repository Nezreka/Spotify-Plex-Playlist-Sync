# config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR.parent / '.env'

# Load environment variables
load_dotenv(ENV_FILE)

# Database
DATABASE_URL = f"sqlite:///{BASE_DIR.parent}/spotify_plex_sync.db"

# API Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Application Settings
APP_NAME = "Spotify to Plex Sync"
APP_VERSION = "1.0.0"
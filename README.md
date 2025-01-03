
# Spotify to Plex Playlist Sync


![Alt text](https://i.imgur.com/Q6ST4Sw.png)


An intelligent Python tool that converts Spotify playlists to Plex playlists, featuring advanced track matching and AI-assisted matching via Claude.

## Features

- **Intelligent Track Matching**: Uses multiple matching strategies including direct matches, similarity matching, and AI-assisted matching
- **Handles Various Track Formats**: 
  - Special characters and abbreviations (e.g., "T.N.T" vs "TNT")
  - Remixes and alternate versions
  - Various artist formats (feat., ft., featuring)
  - Live versions detection
- **AI-Assisted Matching**: Uses Claude AI for complex matching cases
- **Backup and Logging**:
  - Automatically backs up playlist data before modifications
  - Logs unmatched tracks for review
  - Detailed matching statistics
- **Error Handling**: 
  - Robust error handling and retry logic for API calls
  - Detailed logging for troubleshooting

## Prerequisites

- Python 3.8+
- Plex Media Server with a music library
- Plex authentication token
- Claude API key (optional, for AI-assisted matching)
- Spotify API ID & Secret

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Nezreka/Spotify-Plex-Playlist-Sync.git
cd spotify-plex-playlist-sync
```

2. Install required packages:
  All packages installed already. I borked the upload process.
  You may need to install the requirements.txt anyway.

For Macos you will will use pip3 and python3 to install / run the app.

Required callback is: http://localhost:8888/callback

You can change this to any you prefer in spotify_service.py


## Configuration



3. Set up environment variables:
```bash
PLEX_URL=http://your-plex-server:32400
PLEX_TOKEN=your-plex-token
ANTHROPIC_API_KEY=your-claude-api-key  # Optional
Spotify_Secret="Spotify secret"
Spotify_ID="Spotify ID"
```

## Usage
1. UPDATE .env FILE!
2. Enter virtual environment in project directory - venv\scripts\activate
3. run python main.py

## Track Matching Process

1. **Direct Matching**:
   - Exact title and artist matches
   - Normalized string comparison

2. **Similarity Matching**:
   - Title similarity scoring
   - Artist name variations
   - Remix and version handling

3. **Advanced Matching**:
   - Abbreviated title matching
   - First word matching
   - Base title matching

4. **AI-Assisted Matching** (requires Claude API key):
   - Used for complex cases
   - Handles various title/artist formats
   - Makes intelligent matching decisions

## Directory Structure

```
spotify-to-plex-playlist/
├── plex_service.py      # Main service class
├── backups/             # Playlist backups
├── logs/               # Unmatched tracks logs
├── requirements.txt    # Package requirements
└── README.md          # Documentation
```

## Backup and Logging

- **Backups**: Created automatically before playlist modifications
  - Location: `backups/playlist_backup_[name]_[timestamp].json`
  - Contains original track information

- **Unmatched Tracks**: Logged for review
  - Location: `logs/unmatched_tracks_[name]_[timestamp].txt`
  - Includes track details and Spotify URLs

## Error Handling

- Automatic retry for API calls with exponential backoff
- Detailed error logging
- Graceful handling of various edge cases

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

MIT License



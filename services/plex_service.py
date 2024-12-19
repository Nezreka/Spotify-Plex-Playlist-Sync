from plexapi.server import PlexServer
from plexapi.playlist import Playlist
import os
import re
from difflib import SequenceMatcher
from anthropic import Anthropic
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from pathlib import Path


class PlexService:
    def __init__(self, base_url=None, token=None):
        self.base_url = base_url or os.getenv('PLEX_URL')
        self.token = token or os.getenv('PLEX_TOKEN')
        self.server = None
        # Create directories if they don't exist
        Path('backups').mkdir(exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        self.connect()

    def backup_playlist(self, playlist_name, tracks):
        """Backup playlist data before making changes"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Convert tracks to a serializable format, handling both Spotify and Plex tracks
        track_data = []
        for track in tracks:
            if hasattr(track, 'artists'):  # Spotify track
                track_info = {
                    'title': track.title,
                    'artists': track.artists
                }
            else:  # Plex track
                track_info = {
                    'title': track.title,
                    'artist': track.grandparentTitle if hasattr(track, 'grandparentTitle') else 'Unknown'
                }
            track_data.append(track_info)

        backup = {
            'name': playlist_name,
            'timestamp': timestamp,
            'tracks': track_data
        }
        
        backup_file = f'backups/playlist_backup_{playlist_name}_{timestamp}.json'
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup, f, indent=2)
        print(f"Playlist backup created: {backup_file}")

    def log_unmatched_tracks(self, playlist_name, unmatched_tracks):
        """Save unmatched tracks to a log file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f'logs/unmatched_tracks_{playlist_name}_{timestamp}.txt'
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Unmatched tracks for playlist: {playlist_name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n\n")
            
            for track in unmatched_tracks:
                f.write(f"Title: {track.title}\n")
                f.write(f"Artists: {track.artists}\n")
                f.write(f"Spotify URL: {track.url if hasattr(track, 'url') else 'N/A'}\n")
                f.write("\n")
        
        print(f"Unmatched tracks logged to: {log_file}")

    def normalize_string(self, s):
        """Normalize a string by removing special characters and extra whitespace"""
        if s is None:
            return ""
        # Handle periods in abbreviations (e.g., "T.N.T")
        s = s.replace('.', '')  # Remove periods
        # Remove special characters and replace with space
        s = re.sub(r'[^\w\s-]', ' ', s)
        # Replace multiple spaces with single space
        s = re.sub(r'\s+', ' ', s)
        # Convert to lowercase and strip
        return s.lower().strip()

    def normalize_featuring(self, s):
        """Normalize featuring artist formats"""
        if s is None:
            return ""
        # Normalize different featuring formats
        s = re.sub(r'\(?feat\.?\s', 'feat ', s, flags=re.IGNORECASE)
        s = re.sub(r'\(?ft\.?\s', 'feat ', s, flags=re.IGNORECASE)
        s = re.sub(r'\(?featuring\s', 'feat ', s, flags=re.IGNORECASE)
        return s

    def normalize_remix_title(self, title):
        """Normalize remix titles to a standard format"""
        # First normalize the basic string
        title = self.normalize_string(title)
        
        # Define common remix patterns
        remix_patterns = [
            (r'\s*[-–]\s*(.*?mix)', r' \1'),  # Convert "- XXX Mix" to "XXX Mix"
            (r'\s*[-–]\s*(remix)', r' \1'),    # Convert "- Remix" to "Remix"
            (r'\s*[-–]\s*(edit)', r' \1'),     # Convert "- Edit" to "Edit"
            (r'\s*[-–]\s*(version)', r' \1'),  # Convert "- Version" to "Version"
        ]
        
        # Apply each pattern
        normalized = title
        for pattern, replacement in remix_patterns:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Remove parentheses
        normalized = re.sub(r'[\(\)]', '', normalized)
        
        print(f"Normalized remix title: '{title}' -> '{normalized}'")
        return normalized
    
    def title_similarity(self, title1, title2):
        """Calculate similarity between two titles"""
        return SequenceMatcher(None, title1, title2).ratio()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def connect(self):
        """Connect to Plex server"""
        try:
            print(f"Connecting to Plex server at {self.base_url}")
            self.server = PlexServer(self.base_url, self.token)
            print(f"Successfully connected to Plex server: {self.server.friendlyName}")
            return True
        except Exception as e:
            print(f"Failed to connect to Plex server: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_music_library(self):
        """Get the music library section"""
        try:
            music_lib = self.server.library.section('Music')
            return music_lib
        except Exception as e:
            print(f"Failed to get music library: {str(e)}")
            raise
    
    def is_live_version(self, title):
        """Check if a track is a live version"""
        live_indicators = [
            '(live)',
            '(live at',
            '(live in',
            '(recorded live',
            '(performed live',
            '- live',
            '- live at',
            '- live in'
        ]
        normalized_title = self.normalize_string(title).lower()
        return any(indicator in normalized_title for indicator in live_indicators)

    def find_track(self, title, artists_string):
        try:
            music_lib = self.get_music_library()
            artists = [artist.strip() for artist in artists_string.split(',')]
            primary_artist = artists[0] if artists else ""
            
            # Normalize the search title and artist
            normalized_search_title = self.normalize_string(title)
            normalized_remix_title = self.normalize_remix_title(title)
            normalized_search_artist = self.normalize_string(primary_artist)
            
            print(f"\nSearching for: '{title}' by '{artists_string}'")
            print(f"Normalized title: '{normalized_search_title}'")
            print(f"Normalized remix: '{normalized_remix_title}'")
            print(f"Normalized artist: '{normalized_search_artist}'")

            potential_matches = []
            
            # Regular search with retry logic
            tracks = self.get_music_library().search(title=normalized_search_title, libtype='track') or []
            if not tracks:
                tracks = self.get_music_library().search(title=title, libtype='track') or []
            if not tracks:
                base_title = re.sub(r'\s*[-–(].*$', '', title).strip()
                tracks = self.get_music_library().search(title=base_title, libtype='track') or []

            print(f"Found {len(tracks)} potential tracks")
            
            # Try standard matching first
            for track in tracks:
                track_title = self.normalize_string(track.title)
                track_title_remix = self.normalize_remix_title(track.title)
                track_artist = self.normalize_string(track.grandparentTitle if hasattr(track, 'grandparentTitle') else '')
                
                print(f"\nComparing track:")
                print(f"  Spotify: '{title}' -> '{normalized_search_title}'")
                print(f"  Plex:    '{track.title}' -> '{track_title}'")
                print(f"  Artist (Spotify): '{primary_artist}' -> '{normalized_search_artist}'")
                print(f"  Artist (Plex):    '{track.grandparentTitle}' -> '{track_artist}'")
                
                # Calculate base similarity
                title_score = max(
                    self.title_similarity(track_title, normalized_search_title),
                    self.title_similarity(track_title_remix, normalized_remix_title)
                )
                artist_score = max(
                    self.title_similarity(track_artist, self.normalize_string(artist))
                    for artist in artists
                )
                
                print(f"  Similarity scores - Title: {title_score:.2f}, Artist: {artist_score:.2f}")

                # Direct matches (case-insensitive)
                direct_title_match = (
                    title.lower() == track.title.lower() or
                    normalized_search_title == track_title or
                    normalized_remix_title == track_title_remix
                )
                
                direct_artist_match = any(
                    artist.lower() == track.grandparentTitle.lower() 
                    for artist in artists
                )
                
                # High similarity matches
                title_similarity_match = (
                    title_score > 0.8 or
                    normalized_search_title in track_title or
                    track_title in normalized_search_title or
                    normalized_remix_title in track_title_remix or
                    track_title_remix in normalized_remix_title
                )
                
                artist_similarity_match = (
                    artist_score > 0.8 or
                    any(self.normalize_string(artist) in track_artist for artist in artists) or
                    any(track_artist in self.normalize_string(artist) for artist in artists) or
                    (track.grandparentTitle == 'Various Artists' and
                    hasattr(track, 'originalTitle') and
                    any(artist.lower() in track.originalTitle.lower() for artist in artists))
                )
                
                if (direct_title_match and direct_artist_match) or (title_similarity_match and artist_similarity_match):
                    match_score = title_score + artist_score
                    if direct_title_match and direct_artist_match:
                        match_score += 1.0
                        
                    potential_matches.append({
                        'track': track,
                        'score': match_score,
                        'direct_match': direct_title_match and direct_artist_match
                    })
                    print(f"  ✓ Potential match found (score: {match_score})")
                    print(f"    Direct match: {direct_title_match and direct_artist_match}")
                    print(f"    Similarity match: {title_similarity_match and artist_similarity_match}")
                else:
                    print(f"  ✗ No match")
                    print(f"    Direct title match: {direct_title_match}")
                    print(f"    Direct artist match: {direct_artist_match}")
                    print(f"    Title similarity match: {title_similarity_match}")
                    print(f"    Artist similarity match: {artist_similarity_match}")

            # If we found matches through regular matching, return the best one
            if potential_matches:
                sorted_matches = sorted(
                    potential_matches,
                    key=lambda x: (x['direct_match'], x['score']),
                    reverse=True
                )
                
                best_match = sorted_matches[0]['track']
                print(f"\n✓ Best match found: {best_match.title} by {best_match.grandparentTitle}")
                return best_match

            # If no matches found, try additional matching strategies
            print("\nNo matches found through regular matching, trying additional matching...")

            # Try different search approaches for more potential matches
            search_tracks = []
            
            # Try searching with just the letters for abbreviated titles (e.g., "TNT" for "T.N.T.")
            letters_only = ''.join(c for c in title if c.isalnum())
            print(f"Searching with letters only: {letters_only}")
            letter_tracks = music_lib.search(title=letters_only, libtype='track') or []
            
            # Try searching with first word of title
            first_word = title.split()[0]
            print(f"Searching with first word: {first_word}")
            first_word_tracks = music_lib.search(title=first_word, libtype='track') or []
            
            # Try searching with base title (no special characters)
            base_title = re.sub(r'[^\w\s]', '', title)
            print(f"Searching with base title: {base_title}")
            base_tracks = music_lib.search(title=base_title, libtype='track') or []

            # Combine all results
            all_tracks = letter_tracks + first_word_tracks + base_tracks
            
            # Filter by artist similarity
            search_tracks = [
                t for t in all_tracks 
                if any(
                    self.title_similarity(
                        self.normalize_string(artist), 
                        self.normalize_string(t.grandparentTitle)
                    ) > 0.6 
                    for artist in artists
                )
            ]
            
            # Remove duplicates
            search_tracks = list({t.ratingKey: t for t in search_tracks}.values())

            if search_tracks:
                print(f"\nFound {len(search_tracks)} potential tracks to analyze:")
                track_list = [f"{i}: '{t.title}' by '{t.grandparentTitle}'" 
                            for i, t in enumerate(search_tracks)]
                
                for track in track_list:
                    print(track)

                # Check for exact matches first
                for i, track in enumerate(search_tracks):
                    # Check for exact title match
                    if track.title.lower() == title.lower():
                        # Check if artist matches or if it's Various Artists
                        if (any(artist.lower() in track.grandparentTitle.lower() for artist in artists) or
                            (track.grandparentTitle == 'Various Artists' and
                            hasattr(track, 'originalTitle') and
                            any(artist.lower() in track.originalTitle.lower() for artist in artists))):
                            print(f"Found exact match: {track_list[i]}")
                            return track

                # If no exact match found, try Claude-assisted matching
                print("\nNo exact match found, trying Claude-assisted matching...")
                if not os.getenv('ANTHROPIC_API_KEY'):
                    print("Note: Claude API not configured. Advanced matching unavailable.")
                    return None

                try:
                    anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                    
                    prompt = (
                        f"Given the Spotify track '{title}' by '{artists_string}', "
                        f"find the best matching track from this list and reply ONLY "
                        f"with the index number. If no good match exists, reply with -1.\n\n"
                        f"Note that titles might have variations (e.g., 'T.N.T' could be 'TNT' "
                        f"or 'T N T'), and artist names might differ slightly.\n\n"
                        f"Tracks:\n" + "\n".join(track_list)
                    )

                    print("\nSending request to Claude...")
                    message = anthropic.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=1,
                        temperature=0,
                        system="You are a music matching assistant. Only respond with the index number of the best match.",
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )

                    try:
                        response_content = message.content[0].text.strip()
                        print(f"Claude response: {response_content}")
                        
                        # Handle various negative response formats
                        if response_content in ['-', '-1', 'n/a', 'none']:
                            print("Claude found no suitable match")
                        else:
                            try:
                                match_index = int(response_content)
                                if match_index >= 0 and match_index < len(search_tracks):
                                    print(f"Claude suggested match: {track_list[match_index]}")
                                    return search_tracks[match_index]
                                else:
                                    print("Claude response index out of range")
                            except ValueError:
                                print(f"Could not parse Claude response as integer: {response_content}")

                    except (ValueError, IndexError) as e:
                        print(f"Error processing Claude response: {str(e)}")
                        print(f"Raw response: {message.content}")

                except Exception as e:
                    print(f"Error during Claude-assisted matching: {str(e)}")
                    print(f"Error details: {str(e)}")

            print(f"\n✗ No match found for: {title} by {artists_string}")
            return None
                
        except Exception as e:
            print(f"Error searching for track: {str(e)}")
            print(f"Title: {title}, Artists: {artists_string}")
            return None

    def create_playlist(self, name, tracks=None):
        """Create a new playlist"""
        try:
            if tracks is None or len(tracks) == 0:
                print(f"No tracks provided for playlist '{name}', skipping creation")
                return None

            print(f"Attempting to create/update playlist '{name}' with {len(tracks)} tracks")
            
            # Check if these are Plex tracks or Spotify tracks
            is_plex_track = not hasattr(tracks[0], 'artists') if tracks else False
            
            if not is_plex_track:
                # If these are Spotify tracks, perform matching
                self.backup_playlist(name, tracks)
                matched_tracks = []
                unmatched_tracks = []

                for track in tracks:
                    plex_track = self.find_track(track.title, track.artists)
                    if plex_track:
                        matched_tracks.append(plex_track)
                    else:
                        unmatched_tracks.append(track)

                if unmatched_tracks:
                    self.log_unmatched_tracks(name, unmatched_tracks)
                    print(f"\nWarning: {len(unmatched_tracks)} tracks could not be matched")
                
                tracks_to_add = matched_tracks
            else:
                # If these are already Plex tracks, use them directly
                tracks_to_add = tracks

            if tracks_to_add:
                try:
                    # Check for existing playlist
                    existing = self.server.playlists(title=name)
                    if existing:
                        print(f"Found existing playlist '{name}', updating...")
                        playlist = existing[0]
                        # Clear existing items
                        playlist.removeItems(playlist.items())
                        # Add new items
                        playlist.addItems(tracks_to_add)
                        print(f"Updated playlist '{name}' with {len(tracks_to_add)} tracks")
                    else:
                        print(f"Creating new playlist '{name}'...")
                        playlist = self.server.createPlaylist(
                            title=name,
                            items=tracks_to_add,
                            section=self.get_music_library()
                        )
                        print(f"Successfully created playlist '{name}' with {len(tracks_to_add)} tracks")
                    
                    if not is_plex_track:
                        print(f"\nMatching Summary:")
                        print(f"Total tracks: {len(tracks)}")
                        print(f"Matched: {len(matched_tracks)}")
                        print(f"Unmatched: {len(unmatched_tracks)}")
                        print(f"Success rate: {(len(matched_tracks)/len(tracks))*100:.1f}%")
                    
                    return playlist
                    
                except Exception as e:
                    print(f"Error during playlist creation/update: {str(e)}")
                    print(f"Tracks to add: {[t.title for t in tracks_to_add[:3]]}")
                    raise
            else:
                print("\nNo tracks were matched - playlist not created")
                return None

        except Exception as e:
            print(f"Error creating/updating playlist '{name}': {str(e)}")
            print(f"Number of tracks: {len(tracks) if tracks else 0}")
            print(f"First few tracks: {[t.title for t in tracks[:3]] if tracks else 'None'}")
            raise
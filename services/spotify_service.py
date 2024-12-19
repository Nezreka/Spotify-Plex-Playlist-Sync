# services/spotify_service.py
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PyQt6.QtWidgets import QMessageBox

class SpotifyService:
    def __init__(self):
        self.client = None
        self.initialize_client()

    def initialize_client(self):
        try:
            print("Initializing Spotify client...")  # Debug print
            auth_manager = SpotifyOAuth(
                client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
                redirect_uri='http://localhost:8888/callback',
                scope='playlist-read-private playlist-read-collaborative',
                open_browser=True,
                cache_path='.spotify_cache'
            )
            
            self.client = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test the connection and print user info
            user = self.client.current_user()
            print(f"Successfully connected to Spotify as {user['display_name']}")
            return True
        except Exception as e:
            print(f"Spotify initialization error: {str(e)}")
            return False

    def get_playlists(self):
        try:
            if not self.client:
                raise Exception("Spotify client not initialized")
            
            print("Fetching playlists from Spotify...")  # Debug print
            results = self.client.current_user_playlists()
            print(f"Retrieved {len(results['items'])} playlists")  # Debug print
            
            # Print each playlist name for debugging
            for playlist in results['items']:
                print(f"Found playlist: {playlist['name']}")
            
            return results
        except Exception as e:
            print(f"Error fetching playlists: {str(e)}")
            raise

    def get_playlist_tracks(self, playlist_id):
        try:
            if not self.client:
                raise Exception("Spotify client not initialized")
            
            print(f"SpotifyService: Fetching tracks for playlist {playlist_id}")  # Debug print
            
            tracks = []
            results = self.client.playlist_tracks(playlist_id)
            print(f"SpotifyService: Found {len(results['items'])} tracks")  # Debug print
            tracks.extend(results['items'])
            
            while results['next']:
                results = self.client.next(results)
                tracks.extend(results['items'])
                
            print(f"SpotifyService: Total tracks found: {len(tracks)}")  # Debug print
            return {'items': tracks}
        except Exception as e:
            print(f"SpotifyService Error: {str(e)}")  # Debug print
            raise
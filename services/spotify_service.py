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
                scope='playlist-read-private playlist-read-collaborative user-follow-read user-read-private',
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

    def get_featured_playlists(self):
        """Get Spotify's featured playlists"""
        try:
            if not self.client:
                raise Exception("Spotify client not initialized")
            
            print("Fetching featured playlists from Spotify...")
            results = self.client.featured_playlists()
            print(f"Retrieved {len(results['playlists']['items'])} featured playlists")
            
            return results['playlists']
        except Exception as e:
            print(f"Error fetching featured playlists: {str(e)}")
            raise
    
    def get_made_for_you_playlists(self):
        """Get personalized playlists like Discover Weekly and Release Radar"""
        try:
            if not self.client:
                raise Exception("Spotify client not initialized")
            
            print("Fetching personalized playlists...")
            # Get the user's ID
            user_id = self.client.current_user()['id']
            
            # First, get all playlists - regular and followed
            all_playlists = self.client.current_user_playlists()
            
            # Known "Made For You" playlist names to look for
            made_for_you_names = [
                "Discover Weekly", 
                "Release Radar",
                "Daily Mix",
                "On Repeat",
                "Repeat Rewind",
                "Your Time Capsule"
            ]
            
            made_for_you_playlists = []
            for playlist in all_playlists['items']:
                # Check if playlist name contains any of the Made For You names
                if any(name in playlist['name'] for name in made_for_you_names):
                    made_for_you_playlists.append(playlist)
                    print(f"Found Made For You playlist: {playlist['name']}")
            
            return {'items': made_for_you_playlists}
        except Exception as e:
            print(f"Error fetching Made For You playlists: {str(e)}")
            raise
    
    def get_all_available_playlists(self):
        """Get all playlists including user playlists, followed, and Made For You"""
        try:
            # Get regular user playlists
            user_playlists = self.get_playlists()
            
            # Get Made For You playlists
            made_for_you = self.get_made_for_you_playlists()
            
            # Combine playlists - note some may be duplicated but UI will handle that
            all_playlists = user_playlists['items'] + made_for_you['items']
            
            # Remove duplicates by playlist ID
            unique_playlists = []
            seen_ids = set()
            for playlist in all_playlists:
                if playlist['id'] not in seen_ids:
                    unique_playlists.append(playlist)
                    seen_ids.add(playlist['id'])
            
            return {'items': unique_playlists}
        except Exception as e:
            print(f"Error fetching all playlists: {str(e)}")
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
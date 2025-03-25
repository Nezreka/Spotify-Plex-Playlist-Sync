# ui/main_window.py
import os
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QListWidget, 
                            QProgressBar, QMessageBox, QListWidgetItem, QDialog,
                            QFormLayout, QLineEdit, QDialogButtonBox, QMenu, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from dotenv import load_dotenv
from services.plex_service import PlexService
from services.spotify_service import SpotifyService
from ui.config_dialog import ConfigDialog
from ui.themes import ThemeManager

class PlaylistSyncWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, spotify_service, plex_service, playlists):
        super().__init__()
        self.spotify_service = spotify_service
        self.plex_service = plex_service
        self.playlists = playlists
        self.should_stop = False

    def run(self):
        try:
            total_playlists = len(self.playlists)
            
            for playlist_index, playlist in enumerate(self.playlists):
                if self.should_stop:
                    break

                status_msg = f"Processing playlist: {playlist.playlist_name}"
                self.status.emit(status_msg)
                print(status_msg)

                # Get tracks from Spotify
                spotify_tracks = self.spotify_service.get_playlist_tracks(playlist.playlist_id)
                total_tracks = len(spotify_tracks['items'])
                found_tracks = []

                # Process each track
                for track_index, track_item in enumerate(spotify_tracks['items']):
                    if self.should_stop:
                        break

                    track = track_item['track']
                    if not track:  # Skip unavailable tracks
                        continue

                    track_name = track['name']
                    artists = ", ".join([artist['name'] for artist in track['artists']])
                    
                    status_msg = f"Searching for track: {track_name} - {artists}"
                    self.status.emit(status_msg)
                    print(status_msg)

                    # Search for track in Plex
                    plex_track = self.plex_service.find_track(track_name, artists)
                    if plex_track:
                        print(f"✓ Found match: {plex_track.title} by {plex_track.originalTitle}")
                        found_tracks.append(plex_track)
                    else:
                        print(f"✗ No match found for: {track_name} - {artists}")

                    # Update progress
                    current_progress = int(((playlist_index * total_tracks + track_index + 1) / 
                                         (total_playlists * total_tracks)) * 100)
                    self.progress.emit(current_progress)

                # Create/update playlist in Plex if we found any tracks
                if found_tracks:
                    status_msg = f"Creating playlist in Plex: {playlist.playlist_name} with {len(found_tracks)} tracks"
                    self.status.emit(status_msg)
                    print(status_msg)
                    print(f"First few tracks to be added: {[t.title for t in found_tracks[:3]]}")
                    
                    try:
                        created_playlist = self.plex_service.create_playlist(playlist.playlist_name, found_tracks)
                        if created_playlist:
                            print(f"✓ Successfully created playlist: {playlist.playlist_name}")
                            print(f"Playlist ID: {created_playlist.ratingKey}")
                            print(f"Track count: {len(created_playlist.items())}")
                        else:
                            print(f"⚠ Playlist creation returned None for: {playlist.playlist_name}")
                    except Exception as e:
                        print(f"✗ Failed to create playlist: {str(e)}")
                        print(f"Tracks found: {len(found_tracks)}")
                        print(f"Track details: {[(t.title, t.grandparentTitle) for t in found_tracks[:3]]}")

            self.status.emit("Sync completed")
            self.finished.emit()

        except Exception as e:
            error_msg = f"Sync error: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)

    def stop(self):
        self.should_stop = True
        self.status.emit("Stopping sync...")
        print("Sync stop requested")

class PlaylistItem(QListWidgetItem):
    def __init__(self, playlist):
        super().__init__()
        self.playlist_id = playlist['id']
        self.playlist_name = playlist['name']
        
        # Identify if this is a "Made For You" playlist
        made_for_you_names = [
            "Discover Weekly", 
            "Release Radar",
            "Daily Mix",
            "On Repeat",
            "Repeat Rewind",
            "Your Time Capsule"
        ]
        is_made_for_you = any(name in playlist['name'] for name in made_for_you_names)
        
        # Add an icon/prefix for Made For You playlists
        if is_made_for_you:
            display_text = f"✨ {self.playlist_name}"  # Star emoji to indicate special playlist
        else:
            display_text = self.playlist_name
            
        self.setText(display_text)  # Set the display text
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
        self.setCheckState(Qt.CheckState.Unchecked)
        
        # Set tooltip with additional information for Made For You playlists
        if is_made_for_you:
            self.setToolTip(f"Made For You: {self.playlist_name}")
            # Optional: You could use a different background color too
            # self.setBackground(QColor(230, 230, 250))  # Light purple background

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "dark"  # Default to dark theme
        self.spotify_service = None
        self.init_spotify()
        self.init_ui()
        self.setStyleSheet(ThemeManager.DARK_THEME)
        self.load_playlists()
        self.theme_button.setText("☀️")

    def init_spotify(self):
        try:
            self.spotify_service = SpotifyService()
            if not self.spotify_service.client:
                raise Exception("Failed to initialize Spotify client")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize Spotify: {str(e)}")
            sys.exit(1)

    def init_ui(self):
        self.setWindowTitle("Spotify to Plex Sync")
        self.setMinimumSize(800, 600)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Spotify to Plex Playlist Sync")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        # Theme toggle and config buttons
        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(128, 128, 128, 0.2);
                border-radius: 15px;
            }
        """

        self.theme_button = QPushButton("🌙")
        self.theme_button.setFixedSize(30, 30)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setStyleSheet(button_style)
        
        config_button = QPushButton("⚙️")
        config_button.setFixedSize(30, 30)
        config_button.clicked.connect(self.show_config_dialog)
        config_button.setStyleSheet(button_style)

        header_layout.addStretch()
        header_layout.addWidget(self.theme_button)
        header_layout.addWidget(config_button)
        layout.addLayout(header_layout)

        # Create horizontal layout for playlists and tracks
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)  # Add spacing between containers

        # Playlist list with label (left side)
        playlist_container = QVBoxLayout()
        playlist_label = QLabel("Playlists")
        playlist_label.setStyleSheet("font-weight: bold; padding: 5px;")
        playlist_container.addWidget(playlist_label)

        self.playlist_list = QListWidget()
        self.playlist_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                min-width: 200px;
                max-width: 300px;
            }
            QListWidget::item {
                padding: 5px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background-color: rgba(128, 128, 128, 0.1);
            }
            QListWidget::item:selected {
                background-color: #1db954;
                color: white;
            }
        """)
        self.playlist_list.itemSelectionChanged.connect(self.on_playlist_selection_changed)
        playlist_container.addWidget(self.playlist_list)

        # Create container for playlist
        playlist_widget = QWidget()
        playlist_widget.setLayout(playlist_container)
        playlist_widget.setFixedWidth(300)  # Set fixed width for playlist container

        # Track list with label (right side)
        track_container = QVBoxLayout()
        track_label = QLabel("Tracks")
        track_label.setStyleSheet("font-weight: bold; padding: 5px;")
        track_container.addWidget(track_label)

        self.track_list = QListWidget()
        self.track_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                min-width: 400px;
                background-color: #2a2a2a;
            }
            QListWidget::item {
                padding: 5px;
                margin: 2px 0px;
                color: white;
            }
            QListWidget::item:hover {
                background-color: rgba(128, 128, 128, 0.1);
            }
        """)
        track_container.addWidget(self.track_list)

        # Create container for tracks
        track_widget = QWidget()
        track_widget.setLayout(track_container)

        # Add a vertical line separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #cccccc;")

        # Add everything to the content layout
        content_layout.addWidget(playlist_widget)
        content_layout.addWidget(separator)
        content_layout.addWidget(track_widget, 1)  # Give track list more space

        # Add content layout to main layout
        layout.addLayout(content_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #1db954;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Buttons layout
        button_layout = QHBoxLayout()
        
        button_common_style = """
            QPushButton {
                background-color: #1db954;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ed760;
            }
            QPushButton:pressed {
                background-color: #1aa34a;
            }
            QPushButton:disabled {
                background-color: #b3b3b3;
            }
        """
        
        self.sync_selected_button = QPushButton("Sync Selected")
        self.sync_selected_button.clicked.connect(self.sync_selected)
        self.sync_selected_button.setStyleSheet(button_common_style)
        
        self.sync_all_button = QPushButton("Sync All")
        self.sync_all_button.clicked.connect(self.sync_all)
        self.sync_all_button.setStyleSheet(button_common_style)
        
        self.refresh_button = QPushButton("🔄")
        self.refresh_button.setFixedSize(30, 30)
        self.refresh_button.clicked.connect(self.load_playlists)
        self.refresh_button.setStyleSheet(button_style)

        button_layout.addWidget(self.sync_selected_button)
        button_layout.addWidget(self.sync_all_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        layout.addLayout(button_layout)
    
    def on_playlist_selection_changed(self):
        selected_items = self.playlist_list.selectedItems()
        if selected_items:
            item = selected_items[0]  # Get the first selected item
            print(f"Selection changed to: {item.playlist_name}")  # Debug print
            self.on_playlist_selected(item)

    def load_playlists(self):
        try:
            self.playlist_list.clear()
            print("Fetching playlists...")  # Debug print
            
            # Use the new method to get all available playlists including Made For You
            playlists = self.spotify_service.get_all_available_playlists()
            
            print(f"Found {len(playlists['items'])} playlists")  # Debug print
            
            # Group playlists by type for better organization
            regular_playlists = []
            made_for_you_playlists = []
            
            # Known "Made For You" playlist names to categorize
            made_for_you_names = [
                "Discover Weekly", 
                "Release Radar",
                "Daily Mix",
                "On Repeat",
                "Repeat Rewind",
                "Your Time Capsule"
            ]
            
            # Sort playlists into categories
            for playlist in playlists['items']:
                if any(name in playlist['name'] for name in made_for_you_names):
                    made_for_you_playlists.append(playlist)
                else:
                    regular_playlists.append(playlist)
            
            # Add Made For You playlists first (they're special)
            if made_for_you_playlists:
                for playlist in made_for_you_playlists:
                    print(f"Adding Made For You playlist: {playlist['name']}")  # Debug print
                    item = PlaylistItem(playlist)
                    self.playlist_list.addItem(item)
            
            # Then add regular playlists
            for playlist in regular_playlists:
                print(f"Adding playlist: {playlist['name']}")  # Debug print
                item = PlaylistItem(playlist)
                self.playlist_list.addItem(item)
                
        except Exception as e:
            print(f"Error loading playlists: {str(e)}")  # Debug print
            QMessageBox.critical(self, "Error", f"Failed to load playlists: {str(e)}")

    def sync_selected(self):
        selected_playlists = []
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_playlists.append(item)  # Pass the entire PlaylistItem object
        
        if not selected_playlists:
            QMessageBox.warning(self, "Warning", "No playlists selected!")
            return
        
        self.start_sync(selected_playlists)

    def sync_all(self):
        playlists = []
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            playlists.append(item)  # Pass the entire PlaylistItem object
        
        self.start_sync(playlists)

    def start_sync(self, playlist_items):
        try:
            self.progress_bar.show()
            self.sync_selected_button.setEnabled(False)
            self.sync_all_button.setEnabled(False)
            
            # Initialize Plex service
            self.plex_service = PlexService()
            
            # Create and start worker
            self.worker = PlaylistSyncWorker(
                spotify_service=self.spotify_service,
                plex_service=self.plex_service,
                playlists=playlist_items
            )
            self.worker.progress.connect(self.progress_bar.setValue)
            self.worker.status.connect(self.update_status)
            self.worker.finished.connect(self.sync_finished)
            self.worker.error.connect(self.sync_error)
            self.worker.start()
            
        except Exception as e:
            self.sync_error(str(e))

    def update_status(self, message):
        self.statusBar().showMessage(message)

    def sync_finished(self):
        self.progress_bar.hide()
        self.sync_selected_button.setEnabled(True)
        self.sync_all_button.setEnabled(True)
        QMessageBox.information(self, "Success", "Playlist sync completed!")

    def sync_error(self, error_message):
        self.progress_bar.hide()
        self.sync_selected_button.setEnabled(True)
        self.sync_all_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Sync failed: {error_message}")

    def show_config_dialog(self):
        dialog = ConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload environment variables
            load_dotenv(override=True)
            # Reinitialize Spotify
            self.init_spotify()
            # Reload playlists
            self.load_playlists()

    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme_button.setText("☀️")
            self.setStyleSheet(ThemeManager.DARK_THEME)
        else:
            self.current_theme = "light"
            self.theme_button.setText("🌙")
            self.setStyleSheet(ThemeManager.LIGHT_THEME)

    def on_playlist_selected(self, item):
        print("Playlist selected:", item.playlist_name)  # Add this line

        try:
            self.track_list.clear()
            print(f"Loading tracks for playlist: {item.playlist_name}")
            
            # Show loading indicator
            loading_item = QListWidgetItem("Loading tracks...")
            self.track_list.addItem(loading_item)
            
            # Fetch tracks
            results = self.spotify_service.get_playlist_tracks(item.playlist_id)
            self.track_list.clear()  # Clear loading indicator
            
            # Add tracks to list
            for track_item in results['items']:
                track = track_item['track']
                if track:  # Check if track exists (might be None for unavailable tracks)
                    artists = ", ".join([artist['name'] for artist in track['artists']])
                    track_name = track['name']
                    duration_ms = track['duration_ms']
                    duration_min = duration_ms // 60000
                    duration_sec = (duration_ms % 60000) // 1000
                    
                    # Format track info
                    track_info = f"{track_name} - {artists} ({duration_min}:{duration_sec:02d})"
                    list_item = QListWidgetItem(track_info)
                    list_item.setToolTip(track_info)  # Show full info on hover
                    self.track_list.addItem(list_item)
                    
        except Exception as e:
            print(f"Error loading tracks: {str(e)}")
            self.track_list.clear()
            error_item = QListWidgetItem(f"Error loading tracks: {str(e)}")
            self.track_list.addItem(error_item)

    def clear_spotify_cache(self):
        try:
            if os.path.exists('.spotify_cache'):
                os.remove('.spotify_cache')
                print("Cleared Spotify cache")
        except Exception as e:
            print(f"Error clearing cache: {str(e)}")
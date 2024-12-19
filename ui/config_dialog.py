# ui/config_dialog.py
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel,
                           QLineEdit, QDialogButtonBox, QMessageBox, QMenu)
from dotenv import load_dotenv

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setMinimumWidth(400)
        self.init_ui()
        self.load_current_config()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout for inputs
        form = QFormLayout()
        
        # Spotify section
        spotify_label = QLabel("Spotify Configuration")
        spotify_label.setStyleSheet("font-weight: bold;")
        form.addRow(spotify_label)
        
        self.spotify_id = QLineEdit()
        self.spotify_secret = QLineEdit()
        self.spotify_secret.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("Client ID:", self.spotify_id)
        form.addRow("Client Secret:", self.spotify_secret)
        
        # Plex section
        plex_label = QLabel("\nPlex Configuration")
        plex_label.setStyleSheet("font-weight: bold;")
        form.addRow(plex_label)
        
        self.plex_url = QLineEdit()
        self.plex_token = QLineEdit()
        self.plex_token.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("Server URL:", self.plex_url)
        form.addRow("Token:", self.plex_token)
        
        # Anthropic section
        anthropic_label = QLabel("\nAnthropic Configuration")
        anthropic_label.setStyleSheet("font-weight: bold;")
        form.addRow(anthropic_label)
        
        self.anthropic_key = QLineEdit()
        self.anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("API Key:", self.anthropic_key)
        
        layout.addLayout(form)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_config)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_current_config(self):
        self.spotify_id.setText(os.getenv('SPOTIFY_CLIENT_ID', ''))
        self.spotify_secret.setText(os.getenv('SPOTIFY_CLIENT_SECRET', ''))
        self.plex_url.setText(os.getenv('PLEX_URL', ''))
        self.plex_token.setText(os.getenv('PLEX_TOKEN', ''))
        self.anthropic_key.setText(os.getenv('ANTHROPIC_API_KEY', ''))

    def save_config(self):
        env_vars = {
            'SPOTIFY_CLIENT_ID': self.spotify_id.text(),
            'SPOTIFY_CLIENT_SECRET': self.spotify_secret.text(),
            'PLEX_URL': self.plex_url.text(),
            'PLEX_TOKEN': self.plex_token.text(),
            'ANTHROPIC_API_KEY': self.anthropic_key.text()
        }
        
        env_content = '\n'.join(f'{k}={v}' for k, v in env_vars.items() if v)
        
        try:
            with open('.env', 'w') as f:
                f.write(env_content)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
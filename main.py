# main.py
import sys
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # Load environment variables
    load_dotenv()

    # Check required environment variables
    required_vars = ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        sys.exit(1)

    # Create and start the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
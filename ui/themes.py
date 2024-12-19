class ThemeManager:
    DARK_THEME = """
        QMainWindow {
            background-color: #121212;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
        }
        QListWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #333333;
            border-radius: 4px;
        }
        QPushButton {
            background-color: #1db954;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1ed760;
        }
        QPushButton[flat="true"] {
            background-color: transparent;
            color: #ffffff;
        }
        QPushButton[flat="true"]:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        QProgressBar {
            border: 1px solid #333333;
            border-radius: 4px;
            text-align: center;
            color: #ffffff;
        }
        QProgressBar::chunk {
            background-color: #1db954;
        }
    """

    LIGHT_THEME = """
        QMainWindow {
            background-color: #f0f0f0;
            color: #000000;
        }
        QLabel {
            color: #000000;
        }
        QListWidget {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        QPushButton {
            background-color: #1db954;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1ed760;
        }
        QPushButton[flat="true"] {
            background-color: transparent;
            color: #000000;
        }
        QPushButton[flat="true"]:hover {
            background-color: rgba(0, 0, 0, 0.1);
        }
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
            color: #000000;
        }
        QProgressBar::chunk {
            background-color: #1db954;
        }
    """
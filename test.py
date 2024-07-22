from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon
import sys
import os

def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    absolute_path = os.path.join(base_path, relative_path)
    print(f"Resource path for {relative_path}: {absolute_path}")
    return absolute_path

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Window Icon")
        self.setGeometry(100, 100, 300, 200)
        
        # Set the window icon
        icon_path = resource_path("icons/main.png")
        print(f"Setting window icon from: {icon_path}")
        icon = QIcon(icon_path)
        if icon.isNull():
            print("Failed to load icon")
        else:
            print("Icon loaded successfully")
        self.setWindowIcon(icon)
        
        # Set the window file path to ensure the icon is shown on macOS
        self.setWindowFilePath(icon_path)
        self.show()

def main():
    app = QApplication(sys.argv)
    icon_path = resource_path("icons/main.png")
    print(f"Setting application icon from: {icon_path}")
    app.setWindowIcon(QIcon(icon_path))  # Set the application icon
    window = TestWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

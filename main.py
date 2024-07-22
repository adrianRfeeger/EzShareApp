from PySide6.QtWidgets import QApplication
from gui import ezShareCPAP
import sys
from utils import is_dark_mode, load_stylesheet, resource_path
from PySide6.QtGui import QIcon

def main():
    app = QApplication(sys.argv)
    icon_path = resource_path("icons/main.png")
    print(f"Setting application icon from: {icon_path}")
    app.setWindowIcon(QIcon(icon_path))  # Set the application icon
    window = ezShareCPAP()
    
    # Set the window file path to ensure the icon is shown on macOS
    window.setWindowFilePath(icon_path)

    # Detect macOS dark mode and load the appropriate stylesheet
    if is_dark_mode():
        stylesheet = load_stylesheet(resource_path("style_dark.qss"))
    else:
        stylesheet = load_stylesheet(resource_path("style_light.qss"))
        
    app.setStyleSheet(stylesheet)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

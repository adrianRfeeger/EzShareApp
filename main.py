# main.py
from PySide6.QtWidgets import QApplication
from gui import ezShareCPAP
import sys
from utils import is_dark_mode, load_stylesheet

def main():
    app = QApplication(sys.argv)
    window = ezShareCPAP()

    # Detect macOS dark mode and load the appropriate stylesheet
    if is_dark_mode():
        stylesheet = load_stylesheet("style_dark.qss")
    else:
        stylesheet = load_stylesheet("style_light.qss")
        
    app.setStyleSheet(stylesheet)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

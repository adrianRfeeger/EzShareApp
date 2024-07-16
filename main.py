from PySide6.QtWidgets import QApplication
from gui import ezShareCPAP
import sys

def main():
    app = QApplication(sys.argv)
    window = ezShareCPAP()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

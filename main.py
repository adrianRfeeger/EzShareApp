#!/usr/bin/env python3
from PyQt6.QtWidgets import QApplication
from gui import EzShareCPAP
import sys

def main():
    app = QApplication(sys.argv)
    window = EzShareCPAP()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

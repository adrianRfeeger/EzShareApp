#!/usr/bin/env python3
from PyQt6.QtWidgets import QApplication
from gui import EzShareApp
import sys

def main():
    app = QApplication(sys.argv)
    window = EzShareApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

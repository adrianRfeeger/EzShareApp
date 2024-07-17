import os
import subprocess
import sys
from PySide6.QtWidgets import QFileDialog, QMessageBox

def is_dark_mode():
    try:
        result = subprocess.run(
            ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
            capture_output=True, text=True, check=True)
        return 'Dark' in result.stdout
    except subprocess.CalledProcessError:
        return False

def load_stylesheet(file_path):
    with open(file_path, "r") as file:
        return file.read()

def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def ensure_disk_access(directory, parent):
    expanded_directory = os.path.expanduser(directory)
    if not os.path.exists(expanded_directory):
        try:
            os.makedirs(expanded_directory)
        except PermissionError:
            request_disk_access(parent)

def check_disk_access(directory):
    expanded_directory = os.path.expanduser(directory)
    try:
        os.listdir(expanded_directory)
        return True
    except PermissionError:
        return False

def request_disk_access(parent):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    directory = QFileDialog.getExistingDirectory(parent, "Select Directory for Disk Access", "", options=options)
    if directory:
        parent.config['Settings']['path'] = directory
        parent.save_config()
        print(f"Directory selected: {directory}")
    else:
        print("No directory selected")

def request_accessibility_access(parent):
    QMessageBox.information(parent, 'Accessibility Access',
                            'Please enable accessibility access for this application in System Preferences.')
    subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])

def check_oscar_installed():
    """Check if OSCAR is installed on the system."""
    oscar_installed = subprocess.run(["osascript", "-e", 'id of application "OSCAR"'], capture_output=True, text=True)
    return oscar_installed.returncode == 0

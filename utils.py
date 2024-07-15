import os
import subprocess
import sys
from PyQt6.QtWidgets import QFileDialog, QMessageBox

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

def ensure_accessibility_access(parent):
    if not check_accessibility_access():
        request_accessibility_access(parent)

def check_accessibility_access():
    script = '''
    tell application "System Events"
        set isEnabled to UI elements enabled
    end tell
    return isEnabled
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip() == "true"

def request_accessibility_access(parent):
    script = '''
    tell application "System Preferences"
        reveal anchor "Privacy_Accessibility" of pane id "com.apple.preference.security"
        activate
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
    QMessageBox.information(parent, 'Accessibility Access',
                            'Please enable accessibility access for this application in System Preferences.')

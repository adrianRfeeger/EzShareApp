from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
import configparser
import os
import sys
import pathlib
import subprocess
import time
import requests
from ezshare import ezShare
from wifi import connect_to_wifi, disconnect_from_wifi, wifi_connected
from ui_main import Ui_ezShareCPAP

# Utility to get the absolute path to a resource
def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Utility to expand a path
def expand_path(path):
    try:
        expanded_path = pathlib.Path(path).expanduser()
        return expanded_path
    except RuntimeError as e:
        raise

# Worker thread for running the ezShare process
class ezShareWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str, str)  # Added second parameter for message type (info/error)
    finished = pyqtSignal()

    def __init__(self, ezshare):
        super().__init__()
        self.ezshare = ezshare
        self._is_running = True

    def run(self):
        self.ezshare.set_progress_callback(self.update_progress)
        self.ezshare.set_status_callback(self.update_status)
        try:
            connect_to_wifi(self.ezshare)  # Connect to Wi-Fi before starting the process
            self.ezshare.run()
        except RuntimeError as e:
            self.update_status(f'Error: {e}', 'error')
        finally:
            disconnect_from_wifi(self.ezshare)  # Disconnect from Wi-Fi after the process completes
            self.finished.emit()

    def update_progress(self, value):
        self.progress.emit(value)

    def update_status(self, message, message_type='info'):
        self.status.emit(message, message_type)

    def stop(self):
        self._is_running = False
        self.terminate()  # Forcefully terminate the thread
        disconnect_from_wifi(self.ezshare)  # Ensure Wi-Fi is disconnected when stopping
        self.ezshare.disconnect_from_wifi()

# Main window class for the GUI
class ezShareCPAP(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = resource_path('config.ini')
        self.default_config = self.load_default_config()
        self.config = configparser.ConfigParser()
        self.ui = Ui_ezShareCPAP()
        self.ui.setupUi(self)
        self.load_config()  # Load config after setting up the UI
        self.ezshare = ezShare()
        self.worker = None
        self.initUI()
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.reset_status)
        self.is_running = False  # Track the status of the download process

    def initUI(self):
        # Connect buttons to functions
        self.ui.pathBrowseBtn.clicked.connect(self.browse_path)
        self.ui.pathField.mousePressEvent = self.open_path_location  # Override mouse press event
        self.ui.startBtn.clicked.connect(self.start_process)
        self.ui.saveBtn.clicked.connect(self.save_config)
        self.ui.defaultBtn.clicked.connect(self.restore_defaults)
        self.ui.cancelBtn.clicked.connect(self.cancel_process)
        self.ui.quitBtn.clicked.connect(self.close_event_handler)
        self.ui.ezShareConfigBtn.clicked.connect(self.ez_share_config)  # Connect ez Share Config button

        # Set initial values from config
        self.ui.pathField.setText(self.config['Settings']['path'])
        self.ui.urlEntry.setText(self.config['Settings']['url'])
        self.ui.ssidEntry.setText(self.config['WiFi']['ssid'])
        self.ui.pskEntry.setText(self.config['WiFi']['psk'])
        self.ui.importOscarCheckbox.setChecked(self.config['Settings'].getboolean('import_oscar', False))
        self.ui.quitCheckbox.setChecked(self.config['Settings'].getboolean('quit_after_completion', False))

    def browse_path(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        options = dialog.options()
        directory = dialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory:
            self.ui.pathField.setText(directory)

    def open_path_location(self, event):
        path = self.ui.pathField.text()
        expanded_path = expand_path(path)
        if expanded_path.is_dir():
            subprocess.run(['open', expanded_path])  # Use 'open' command to open the directory on macOS

    def start_process(self):
        path = self.ui.pathField.text()
        url = self.ui.urlEntry.text()
        ssid = self.ui.ssidEntry.text()
        psk = self.ui.pskEntry.text()

        if not path or not url or not ssid:
            self.update_status('Input Error: All fields must be filled out.', 'error')
            return

        try:
            expanded_path = expand_path(path)
        except RuntimeError as e:
            self.update_status(f'Could not determine home directory: {e}', 'error')
            return

        if not expanded_path.is_dir():
            self.update_status('Invalid Path: The specified path does not exist or is not a directory.', 'error')
            return

        self.config['Settings']['path'] = str(expanded_path)
        self.config['Settings']['url'] = url
        self.config['WiFi']['ssid'] = ssid
        self.config['WiFi']['psk'] = psk
        self.config['Settings']['import_oscar'] = str(self.ui.importOscarCheckbox.isChecked())
        self.config['Settings']['quit_after_completion'] = str(self.ui.quitCheckbox.isChecked())

        self.ezshare.set_params(
            path=expanded_path,
            url=url,
            start_time=None,
            show_progress=True,
            verbose=True,
            overwrite=False,
            keep_old=False,
            ssid=ssid,
            psk=psk,
            ignore=[],
            retries=3,
            connection_delay=5,
            debug=True
        )

        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.worker = ezShareWorker(self.ezshare)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()
        self.is_running = True  # Set the flag to indicate the process is running

    def update_progress(self, value):
        self.ui.progressBar.setValue(value)

    def update_status(self, message, message_type='info'):
        if message_type == 'error':
            self.ui.statusLabel.setStyleSheet("color: red;")
        else:
            self.ui.statusLabel.setStyleSheet("")  # Reset to default color
        self.ui.statusLabel.setText(message)
        if message_type != 'info':  # Start the timer only if the message type is not 'info'
            self.status_timer.start(5000)  # Reset status to "Ready." after 5 seconds

    def reset_status(self):
        if not self.is_running:  # Only reset the status if the process is not running
            self.update_status('Ready.', 'info')

    def process_finished(self):
        self.update_status('Ready.', 'info')
        self.ui.progressBar.setValue(0)
        if self.ui.importOscarCheckbox.isChecked():
            self.import_cpap_data_with_oscar()
        if self.ui.quitCheckbox.isChecked():
            self.close()
        self.is_running = False  # Reset the flag when the process finishes

    def import_cpap_data_with_oscar(self):
        script = '''
        tell application "OSCAR"
            activate
            delay 2
            tell application "System Events"
                tell process "OSCAR"
                    click menu item "Import CPAP Card Data" of menu "File" of menu bar 1
                end tell
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])

    def cancel_process(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()  # Ensure the thread finishes properly
            self.ui.progressBar.setValue(0)
            self.update_status('Process cancelled.', 'info')

    def close_event_handler(self):
        if self.worker and self.worker.isRunning():
            self.cancel_process()
        self.update_status('Ready.', 'info')
        self.ui.progressBar.setValue(0)
        self.close()

    def ez_share_config(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle('ez Share Config')
        msg.setText("To configure the ez Share SD card, the settings page will be opened with your default browser. Ensure that you update the settings in ezShareCPAP with any changes that you make to the SSID or PSK. P.S. the default password is 'admin'.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        ret = msg.exec()

        if ret == QMessageBox.StandardButton.Ok:
            msg.close()
            self.update_status('Starting configuration process...', 'info')
            try:
                self.update_status(f'Connecting to {self.ui.ssidEntry.text()}...', 'info')
                self.ezshare.set_params(
                    path=self.config['Settings']['path'],
                    url=self.config['Settings']['url'],
                    start_time=None,
                    show_progress=True,
                    verbose=True,
                    overwrite=False,
                    keep_old=False,
                    ssid=self.ui.ssidEntry.text(),
                    psk=self.ui.pskEntry.text(),
                    ignore=[],
                    retries=3,
                    connection_delay=5,
                    debug=True
                )
                connect_to_wifi(self.ezshare)

                # Wait for connection to establish
                time.sleep(self.ezshare.connection_delay)

                if wifi_connected(self.ezshare):
                    self.update_status(f'Connected to {self.ui.ssidEntry.text()}.', 'info')
                    self.update_status('Checking if the ez Share HTTP server is reachable...', 'info')
                    try:
                        response = requests.get('http://192.168.4.1/publicdir/index.htm?vtype=0&fdir=&ftype=1&devw=320&devh=356', timeout=5)
                        if response.status_code == 200:
                            self.update_status('HTTP server is reachable. Opening the configuration page...', 'info')
                            subprocess.run(['open', 'http://192.168.4.1/publicdir/index.htm?vtype=0&fdir=&ftype=1&devw=320&devh=356'])
                        else:
                            self.update_status(f'Failed to reach the HTTP server. Status code: {response.status_code}', 'error')
                    except requests.RequestException as e:
                        self.update_status(f'Failed to reach the HTTP server. Error: {e}', 'error')
                else:
                    self.update_status('Failed to connect to the ez Share Wi-Fi.', 'error')
            except RuntimeError as e:
                self.update_status(f'Error: {e}', 'error')
        else:
            self.update_status('Configuration cancelled.', 'info')

    def closeEvent(self, event):
        self.close_event_handler()
        event.accept()

    def load_default_config(self):
        default_config = configparser.ConfigParser()
        default_config['Settings'] = {
            'path': '~/Documents/CPAP_Data/SD_card',
            'url': 'http://192.168.4.1/dir?dir=A:',
            'start_time': '',
            'show_progress': 'true',
            'verbose': 'true',
            'overwrite': 'false',
            'keep_old': 'false',
            'ignore': '',
            'retries': '3',
            'connection_delay': '5',
            'debug': 'true',
            'import_oscar': 'false',
            'quit_after_completion': 'false'
        }
        default_config['WiFi'] = {
            'ssid': 'ez Share',
            'psk': '88888888'
        }
        return default_config

    def load_config(self):
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as configfile:
                self.default_config.write(configfile)
        self.config.read(self.config_file)

    def save_config(self):
        self.config['Settings']['path'] = self.ui.pathField.text()
        self.config['Settings']['url'] = self.ui.urlEntry.text()
        self.config['WiFi']['ssid'] = self.ui.ssidEntry.text()
        self.config['WiFi']['psk'] = self.ui.pskEntry.text()
        self.config['Settings']['import_oscar'] = str(self.ui.importOscarCheckbox.isChecked())
        self.config['Settings']['quit_after_completion'] = str(self.ui.quitCheckbox.isChecked())
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
        self.update_status('Settings have been saved successfully.', 'info')

    def restore_defaults(self):
        self.config = self.default_config
        self.ui.pathField.setText(self.config["Settings"]["path"])
        self.ui.urlEntry.setText(self.config['Settings']['url'])
        self.ui.ssidEntry.setText(self.config['WiFi']['ssid'])
        self.ui.pskEntry.setText(self.config['WiFi']['psk'])
        self.ui.importOscarCheckbox.setChecked(self.config['Settings'].getboolean('import_oscar', False))
        self.ui.quitCheckbox.setChecked(self.config['Settings'].getboolean('quit_after_completion', False))
        self.update_status('Settings have been restored to defaults.', 'info')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ezShareCPAP()
    ex.show()
    sys.exit(app.exec())

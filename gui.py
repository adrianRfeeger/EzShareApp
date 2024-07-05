from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
import configparser
import os
import sys
import pathlib
import subprocess
from ezShare import ezShare
from wifi import connect_to_wifi, disconnect_from_wifi
from ui_main import Ui_ezShareCPAP

def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def expand_path(path):
    try:
        expanded_path = pathlib.Path(path).expanduser()
        return expanded_path
    except RuntimeError as e:
        raise

class ezShareWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str, str)  # Added second parameter for message type (info/error)
    finished = pyqtSignal()

    def __init__(self, ezShare):
        super().__init__()
        self.ezShare = ezShare
        self._is_running = True

    def run(self):
        self.ezShare.set_progress_callback(self.update_progress)
        self.ezShare.set_status_callback(self.update_status)
        try:
            connect_to_wifi(self.ezShare)  # Connect to Wi-Fi before starting the process
            self.ezShare.run()
        except RuntimeError as e:
            self.update_status(f'Error: {e}', 'error')
        finally:
            disconnect_from_wifi(self.ezShare)  # Disconnect from Wi-Fi after the process completes
            self.finished.emit()

    def update_progress(self, value):
        self.progress.emit(value)

    def update_status(self, message, message_type='info'):
        self.status.emit(message, message_type)

    def stop(self):
        self._is_running = False
        self.terminate()  # Forcefully terminate the thread
        disconnect_from_wifi(self.ezShare)  # Ensure Wi-Fi is disconnected when stopping
        self.ezShare.disconnect_from_wifi()

class ezShareCPAP(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = resource_path('config.ini')
        self.default_config = self.load_default_config()
        self.config = configparser.ConfigParser()
        self.ui = Ui_ezShareCPAP()
        self.ui.setupUi(self)
        self.load_config()  # Load config after setting up the UI
        self.ezShare = ezShare()
        self.worker = None
        self.initUI()
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.reset_status)

    def initUI(self):
        # Connect buttons to functions
        self.ui.pathBrowseBtn.clicked.connect(self.browse_path)
        self.ui.startBtn.clicked.connect(self.start_process)
        self.ui.saveBtn.clicked.connect(self.save_config)
        self.ui.defaultBtn.clicked.connect(self.restore_defaults)
        self.ui.cancelBtn.clicked.connect(self.cancel_process)
        self.ui.quitBtn.clicked.connect(self.close_event_handler)

        # Set initial values from config
        self.ui.pathEntry.setText(self.config['Settings']['path'])
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
            self.ui.pathEntry.setText(directory)

    def start_process(self):
        path = self.ui.pathEntry.text()
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

        self.ezShare.set_params(
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

        self.worker = ezShareWorker(self.ezShare)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()

    def update_progress(self, value):
        self.ui.progressBar.setValue(value)

    def update_status(self, message, message_type='info'):
        if message_type == 'error':
            self.ui.statusLabel.setStyleSheet("color: red;")
        else:
            self.ui.statusLabel.setStyleSheet("")  # Reset to default color
        self.ui.statusLabel.setText(message)
        self.status_timer.start(5000)  # Reset status to "Ready." after 5 seconds

    def reset_status(self):
        self.update_status('Ready.', 'info')

    def process_finished(self):
        self.update_status('Ready.', 'info')
        self.ui.progressBar.setValue(0)
        if self.ui.importOscarCheckbox.isChecked():
            self.import_cpap_data_with_oscar()
        if self.ui.quitCheckbox.isChecked():
            self.close()

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
        self.config['Settings']['path'] = self.ui.pathEntry.text()
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
        self.ui.pathEntry.setText(self.config['Settings']['path'])
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

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QFileDialog, QCheckBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import configparser
import os
import sys
import pathlib
import subprocess
from ezshare import EZShare
from wifi import connect_to_wifi, disconnect_from_wifi

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def shorten_path(path):
    home = pathlib.Path.home()
    try:
        return '~' + str(pathlib.Path(path).relative_to(home))
    except ValueError:
        return str(path)

class EzShareWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str, str)
    finished = pyqtSignal()

    def __init__(self, ezshare):
        super().__init__()
        self.ezshare = ezshare
        self._is_running = True

    def run(self):
        self.ezshare.set_progress_callback(self.update_progress)
        self.ezshare.set_status_callback(self.update_status)
        try:
            connect_to_wifi(self.ezshare)
            self.ezshare.run()
        except RuntimeError as e:
            self.update_status(f'Error: {e}', 'error')
        finally:
            self.ezshare.disconnect_from_wifi()
            self.finished.emit()

    def update_progress(self, value):
        self.progress.emit(value)

    def update_status(self, message, message_type='info'):
        self.status.emit(message, message_type)

    def stop(self):
        self._is_running = False
        self.ezshare.stop()
        self.terminate()
        self.wait()
        if self.ezshare.connected:
            self.ezshare.disconnect_from_wifi()

class EzShareCPAP(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = resource_path('config.ini')
        self.default_config = self.load_default_config()
        self.config = configparser.ConfigParser()
        self.load_config()
        self.ezshare = EZShare()
        self.worker = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('EzShareCPAP')
        self.setWindowIcon(QIcon(resource_path('icon.icns')))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Path
        path_layout = QHBoxLayout()
        self.path_label = QLabel('Path:')
        self.path_entry = QLineEdit(self.config['Settings']['path'])
        self.path_entry.setReadOnly(True)
        self.path_browse_btn = QPushButton('Browse')
        self.path_browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_entry)
        path_layout.addWidget(self.path_browse_btn)

        # URL
        url_layout = QHBoxLayout()
        self.url_label = QLabel('URL:')
        self.url_entry = QLineEdit(self.config['Settings']['url'])
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url_entry)

        # WiFi SSID
        ssid_layout = QHBoxLayout()
        self.ssid_label = QLabel('WiFi SSID:')
        self.ssid_entry = QLineEdit(self.config['WiFi']['ssid'])
        ssid_layout.addWidget(self.ssid_label)
        ssid_layout.addWidget(self.ssid_entry)

        # WiFi PSK
        psk_layout = QHBoxLayout()
        self.psk_label = QLabel('WiFi PSK:')
        self.psk_entry = QLineEdit(self.config['WiFi']['psk'])
        self.psk_entry.setEchoMode(QLineEdit.EchoMode.Password)
        psk_layout.addWidget(self.psk_label)
        psk_layout.addWidget(self.psk_entry)

        # Checkboxes
        self.import_oscar_checkbox = QCheckBox("Import with OSCAR after completion")
        self.import_oscar_checkbox.setChecked(self.config['Settings'].getboolean('import_oscar', False))
        self.quit_checkbox = QCheckBox("Quit after completion")
        self.quit_checkbox.setChecked(self.config['Settings'].getboolean('quit_after_completion', False))

        # Buttons
        btn_layout = QHBoxLayout()
        buttons = [
            ('Start', self.start_process),
            ('Save Settings', self.save_config),
            ('Restore Defaults', self.restore_defaults),
            ('Cancel', self.cancel_process),
            ('Quit', self.close)
        ]
        for label, func in buttons:
            btn = QPushButton(label)
            btn.clicked.connect(func)
            btn_layout.addWidget(btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Status label
        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(path_layout)
        layout.addLayout(url_layout)
        layout.addLayout(ssid_layout)
        layout.addLayout(psk_layout)
        layout.addWidget(self.import_oscar_checkbox)
        layout.addWidget(self.quit_checkbox)
        layout.addLayout(btn_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Timer for status reset
        self.status_timer = QTimer()
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.reset_status)

    def browse_path(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        options = dialog.options()
        directory = dialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory:
            self.path_entry.setText(shorten_path(directory))

    def start_process(self):
        path = self.path_entry.text()
        url = self.url_entry.text()
        ssid = self.ssid_entry.text()
        psk = self.psk_entry.text()

        if not path or not url or not ssid:
            self.update_status('Input Error: All fields must be filled out.', 'error')
            return

        if not pathlib.Path(path).expanduser().is_dir():
            self.update_status('Invalid Path: The specified path does not exist or is not a directory.', 'error')
            return

        self.config['Settings']['path'] = path
        self.config['Settings']['url'] = url
        self.config['WiFi']['ssid'] = ssid
        self.config['WiFi']['psk'] = psk
        self.config['Settings']['import_oscar'] = str(self.import_oscar_checkbox.isChecked())
        self.config['Settings']['quit_after_completion'] = str(self.quit_checkbox.isChecked())

        self.ezshare.set_params(
            path=path,
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

        self.worker = EzShareWorker(self.ezshare)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message, message_type='info'):
        self.status_label.setStyleSheet("color: red;" if message_type == 'error' else "")
        self.status_label.setText(message)

        # Start/reset the timer to revert the status to "Ready."
        self.status_timer.start(3000)  # 3 seconds

    def reset_status(self):
        self.update_status('Ready.', 'info')

    def process_finished(self):
        self.update_status('Ready.', 'info')
        self.progress_bar.setValue(0)
        if self.import_oscar_checkbox.isChecked():
            self.import_cpap_data_with_oscar()
        if self.quit_checkbox.isChecked():
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
            self.worker.wait()
            self.progress_bar.setValue(0)
            self.update_status('Process cancelled.', 'info')

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        self.update_status('Ready.', 'info')
        self.progress_bar.setValue(0)
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
        self.config['Settings']['path'] = self.path_entry.text()
        self.config['Settings']['url'] = self.url_entry.text()
        self.config['WiFi']['ssid'] = self.ssid_entry.text()
        self.config['WiFi']['psk'] = self.psk_entry.text()
        self.config['Settings']['import_oscar'] = str(self.import_oscar_checkbox.isChecked())
        self.config['Settings']['quit_after_completion'] = str(self.quit_checkbox.isChecked())
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
        self.update_status('Settings have been saved successfully.', 'info')

    def restore_defaults(self):
        self.config = self.default_config
        self.path_entry.setText(self.config['Settings']['path'])
        self.url_entry.setText(self.config['Settings']['url'])
        self.ssid_entry.setText(self.config['WiFi']['ssid'])
        self.psk_entry.setText(self.config['WiFi']['psk'])
        self.import_oscar_checkbox.setChecked(self.config['Settings'].getboolean('import_oscar', False))
        self.quit_checkbox.setChecked(self.config['Settings'].getboolean('quit_after_completion', False))
        self.update_status('Settings have been restored to defaults.', 'info')

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ex = EzShareCPAP()
    ex.show()
    sys.exit(app.exec())

from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QProgressBar, QLabel
from PySide6.QtCore import QTimer, QSize, QPoint
import os
import pathlib
import configparser
import subprocess
import time
import requests
from ui_main import Ui_ezShareCPAP
from worker import ezShareWorker
from utils import resource_path, ensure_disk_access, request_accessibility_access, check_oscar_installed, is_dark_mode, load_stylesheet
from wifi import connect_to_wifi, wifi_connected
from ezshare import ezShare

class ezShareCPAP(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = resource_path('config.ini')
        self.config = configparser.ConfigParser()
        self.load_config()
        self.worker = None  # Initialize worker to None
        self.initUI()
        self.request_permissions()
        self.check_oscar_installation(on_launch=True)  # Check for OSCAR installation on launch

    def initUI(self):
        self.ui = Ui_ezShareCPAP()
        self.ui.setupUi(self)

        # Restore window size and position from config
        self.resize(QSize(int(self.config['Window'].get('width', '800')), int(self.config['Window'].get('height', '600'))))
        self.move(QPoint(int(self.config['Window'].get('x', '100')), int(self.config['Window'].get('y', '100'))))

        # Status bar message and progress bar
        self.statusBar().showMessage('Ready.')
        self.progressBar = QProgressBar(self)
        self.progressBar.setMaximumWidth(200)
        self.statusBar().addPermanentWidget(self.progressBar)

        self.ui.pathBrowseBtn.clicked.connect(self.browse_path)
        self.ui.pathField.mousePressEvent = self.open_path_location  # Override mouse press event
        self.ui.startBtn.clicked.connect(self.start_process)
        self.ui.saveBtn.clicked.connect(self.save_config)
        self.ui.defaultBtn.clicked.connect(self.restore_defaults)
        self.ui.cancelBtn.clicked.connect(self.cancel_process)
        self.ui.quitBtn.clicked.connect(self.close_event_handler)
        self.ui.ezShareConfigBtn.clicked.connect(self.ez_share_config)  # Connect ez Share Config button

        # Ensure the text for ezShareConfigBtn is properly set
        self.ui.ezShareConfigBtn.setText("ez Share Config")

        # Connect menu actions
        self.ui.actionLoad_Default.triggered.connect(self.restore_defaults)
        self.ui.actionChange_Path.triggered.connect(self.browse_path)
        self.ui.actionSave_Settings.triggered.connect(self.save_config)
        self.ui.actionQuit.triggered.connect(self.close_event_handler)
        self.ui.actionEz_Share_Config.triggered.connect(self.ez_share_config)
        self.ui.actionCheck_Access_Oscar.triggered.connect(lambda: self.check_oscar_installation(on_launch=False))

        # Set initial values from config
        self.update_path_label(self.config['Settings'].get('path', '~/Documents/CPAP_Data/SD_card'))
        self.ui.urlEntry.setText(self.config['Settings'].get('url', 'http://192.168.4.1/dir?dir=A:'))
        self.ui.ssidEntry.setText(self.config['WiFi'].get('ssid', 'ez Share'))
        self.ui.pskEntry.setText(self.config['WiFi'].get('psk', '88888888'))
        self.ui.quitCheckbox.setChecked(self.config['Settings'].getboolean('quit_after_completion', False))

        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.reset_status)
        self.is_running = False  # Track the status of the download process

        self.apply_stylesheet()

        self.dark_mode_timer = QTimer(self)
        self.dark_mode_timer.timeout.connect(self.apply_stylesheet)
        self.dark_mode_timer.start(5000)  # Check every 5 seconds

    def apply_stylesheet(self):
        if is_dark_mode():
            stylesheet = load_stylesheet("style_dark.qss")
        else:
            stylesheet = load_stylesheet("style_light.qss")
        self.setStyleSheet(stylesheet)

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.config['Settings'] = {
                'path': '~/Documents/CPAP_Data/SD_card',
                'url': 'http://192.168.4.1/dir?dir=A:',
                'accessibility_checked': 'False',
                'accessibility_prompt_disabled': 'False',
                'import_oscar': 'False',
                'quit_after_completion': 'False'
            }
            self.config['WiFi'] = {
                'ssid': 'ez Share',
                'psk': '88888888'
            }
            self.config['Window'] = {
                'width': '800',
                'height': '600',
                'x': '100',
                'y': '100'
            }
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        self.config.read(self.config_file)
        if 'Window' not in self.config:
            self.config['Window'] = {
                'width': '800',
                'height': '600',
                'x': '100',
                'y': '100'
            }

    def save_config(self):
        self.config['Settings']['import_oscar'] = str(self.ui.importOscarCheckbox.isChecked())
        self.config['Settings']['quit_after_completion'] = str(self.ui.quitCheckbox.isChecked())
        # Save window size and position
        self.config['Window']['width'] = str(self.size().width())
        self.config['Window']['height'] = str(self.size().height())
        self.config['Window']['x'] = str(self.pos().x())
        self.config['Window']['y'] = str(self.pos().y())
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
            self.update_status('Settings saved.', 'info')

    def request_permissions(self):
        ensure_disk_access(self.config['Settings']['path'], self)

    def request_accessibility_access(self):
        request_accessibility_access(self)

    def browse_path(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        options = dialog.options()
        directory = dialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory:
            short_path = self.convert_to_short_path(directory)
            self.config['Settings']['path'] = short_path
            self.update_path_label(short_path)

    def convert_to_short_path(self, full_path):
        home_dir = str(pathlib.Path.home())
        if full_path.startswith(home_dir):
            return full_path.replace(home_dir, '~', 1)
        return full_path

    def update_path_label(self, path):
        self.ui.pathField.setText(path)
        self.ui.pathField.setStyleSheet("""
            QLabel {
                border: 1px solid #d1d1d1;
                padding: 5px;
                border-radius: 4px;
                background-color: white;
            }
        """)

    def open_path_location(self, event):
        path = self.config['Settings']['path']
        expanded_path = pathlib.Path(path).expanduser()
        if expanded_path.is_dir():
            subprocess.run(['open', expanded_path])  # Use 'open' command to open the directory on macOS

    def start_process(self):
        path = self.config['Settings']['path']
        url = self.ui.urlEntry.text()
        ssid = self.ui.ssidEntry.text()
        psk = self.ui.pskEntry.text()

        self.update_status('Checking Connections.', 'info')

        if not path or not url or not ssid:
            self.update_status('Input Error: All fields must be filled out.', 'error')
            return

        try:
            expanded_path = pathlib.Path(path).expanduser()
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

        self.ezshare = ezShare()
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

        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.disable_ui_elements()
        self.worker = ezShareWorker(self.ezshare)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()
        self.is_running = True  # Set the flag to indicate the process is running

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def update_status(self, message, message_type='info'):
        current_status = self.statusBar().currentMessage()
        if message != current_status:  # Only update if the message is different
            if message_type == 'error':
                self.statusBar().setStyleSheet("color: red;")
            else:
                self.statusBar().setStyleSheet("")  # Reset to default color
            self.statusBar().showMessage(message)
            if message_type == 'info' and message != 'Ready.':  # Only reset to "Ready." if not running
                self.status_timer.start(5000)  # Reset status to "Ready." after 5 seconds

    def reset_status(self):
        if not self.is_running:  # Only reset the status if the process is not running
            self.update_status('Ready.', 'info')

    def process_finished(self):
        self.is_running = False  # Reset the flag when the process finishes
        self.enable_ui_elements()
        self.progressBar.setValue(0)
        if self.ui.importOscarCheckbox.isChecked():
            self.import_cpap_data_with_oscar()
        if self.ui.quitCheckbox.isChecked():
            self.close()
        else:
            self.update_status('Ready.', 'info')  # Ensure status is set to Ready after process finishes

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
            self.progressBar.setValue(0)
            self.update_status('Process cancelled.', 'info')
        self.is_running = False  # Reset the flag when the process is cancelled
        self.enable_ui_elements()
        if self.ezshare:
            self.ezshare.disconnect_from_wifi()  # Ensure Wi-Fi is disconnected

    def close_event_handler(self):
        if self.worker and self.worker.isRunning():
            self.cancel_process()
        self.update_status('Ready.', 'info')
        self.progressBar.setValue(0)
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

    def restore_defaults(self):
        self.config['Settings'] = {
            'path': '~/Documents/CPAP_Data/SD_card',
            'url': 'http://192.168.4.1/dir?dir=A:',
            'accessibility_checked': 'False',
            'accessibility_prompt_disabled': 'False',
            'import_oscar': 'False',
            'quit_after_completion': 'False'
        }
        self.config['WiFi'] = {
            'ssid': 'ez Share',
            'psk': '88888888'
        }
        self.config['Window'] = {
            'width': '800',
            'height': '600',
            'x': '100',
            'y': '100'
        }
        self.save_config()
        self.load_config()
        self.update_path_label(self.config['Settings'].get('path'))
        self.ui.urlEntry.setText(self.config['Settings'].get('url'))
        self.ui.ssidEntry.setText(self.config['WiFi'].get('ssid'))
        self.ui.pskEntry.setText(self.config['WiFi'].get('psk'))
        self.ui.importOscarCheckbox.setChecked(False)
        self.ui.quitCheckbox.setChecked(False)
        self.update_status('Settings have been restored to defaults.', 'info')

    def update_checkboxes(self):
        oscar_installed = check_oscar_installed()
        self.ui.importOscarCheckbox.setChecked(self.config['Settings'].getboolean('import_oscar', False) and oscar_installed)
        self.ui.importOscarCheckbox.setEnabled(oscar_installed)
        self.ui.downloadOscarLink.setVisible(oscar_installed)
        self.ui.quitCheckbox.setChecked(self.config['Settings'].getboolean('quit_after_completion', False))

    def check_oscar_installation(self, on_launch=True):
        """Check if OSCAR is installed, and update the UI accordingly."""
        oscar_installed = check_oscar_installed()
        if oscar_installed:
            self.ui.importOscarCheckbox.setEnabled(True)
            self.ui.importOscarCheckbox.setChecked(self.config['Settings'].getboolean('import_oscar', False))
            self.ui.downloadOscarLink.setVisible(False)
            if not on_launch:
                self.update_status('OSCAR is installed. Checking accessibility access...', 'info')
                subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
        else:
            self.ui.importOscarCheckbox.setEnabled(False)
            self.ui.importOscarCheckbox.setChecked(False)
            self.ui.downloadOscarLink.setVisible(True)
            if not on_launch:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle('OSCAR Not Installed')
                msg.setText("OSCAR is not currently installed. Would you like to download OSCAR?")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
                msg.setDefaultButton(QMessageBox.StandardButton.Ok)
                ret = msg.exec()
                if ret == QMessageBox.StandardButton.Ok:
                    subprocess.run(['open', 'https://www.sleepfiles.com/OSCAR/'])
                else:
                    self.update_status('OSCAR installation was not initiated.', 'info')

    def disable_ui_elements(self):
        self.ui.pathBrowseBtn.setEnabled(False)
        self.ui.startBtn.setEnabled(False)
        self.ui.saveBtn.setEnabled(False)
        self.ui.defaultBtn.setEnabled(False)
        self.ui.quitBtn.setEnabled(False)
        self.ui.ezShareConfigBtn.setEnabled(False)
        self.ui.menuSettings.setEnabled(False)
        self.ui.menuTools.setEnabled(False)

    def enable_ui_elements(self):
        self.ui.pathBrowseBtn.setEnabled(True)
        self.ui.startBtn.setEnabled(True)
        self.ui.saveBtn.setEnabled(True)
        self.ui.defaultBtn.setEnabled(True)
        self.ui.quitBtn.setEnabled(True)
        self.ui.ezShareConfigBtn.setEnabled(True)
        self.ui.menuSettings.setEnabled(True)
        self.ui.menuTools.setEnabled(True)

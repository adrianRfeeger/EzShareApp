from PySide6.QtCore import QThread, Signal
from wifi import connect_to_wifi, disconnect_from_wifi

class ezShareWorker(QThread):
    progress = Signal(int)
    status = Signal(str, str)  # Added second parameter for message type (info/error)
    finished = Signal()

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
        self.progress.emit(min(max(0, value), 100))  # Ensure progress is between 0 and 100

    def update_status(self, message, message_type='info'):
        self.status.emit(message, message_type)

    def stop(self):
        self._is_running = False
        self.terminate()  # Forcefully terminate the thread
        disconnect_from_wifi(self.ezshare)  # Ensure Wi-Fi is disconnected when stopping
        self.ezshare.disconnect_from_wifi()

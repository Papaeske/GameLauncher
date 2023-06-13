import os
import platform
import requests
import zipfile
import shutil
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QLabel, QMessageBox, QVBoxLayout, QWidget, QProgressBar, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal

class Version:
    def __init__(self, version_str):
        self.major, self.minor, self.sub_minor = map(int, version_str.split('.'))

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.sub_minor}'

    def is_different_than(self, other):
        return (self.major, self.minor, self.sub_minor) != (other.major, other.minor, other.sub_minor)

class DownloadThread(QThread):
    download_progress = pyqtSignal(int)
    download_completed = pyqtSignal(str)

    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url

    def run(self):
        response = requests.get(self.download_url, stream=True)
        file_size = int(response.headers.get('Content-Length', 0))
        block_size = 1024
        progress = 0
        with open('Build.zip', 'wb') as out_file:
            for data in response.iter_content(block_size):
                out_file.write(data)
                progress += len(data)
                self.download_progress.emit(int((float(progress) / file_size) * 100))
        self.download_completed.emit('Build.zip')

class LauncherWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(LauncherWindow, self).__init__(*args, **kwargs)
        self.online_version = None
        self.root_path = os.getcwd()
        self.version_file = os.path.join(self.root_path, "Version.txt")
        self.game_zip = os.path.join(self.root_path, "Build.zip")
        self.play_button = QPushButton("Check for updates")
        self.play_button.clicked.connect(self.check_for_updates)
        self.status_label = QLabel("")
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.play_button)
        self.layout.addWidget(self.status_label)
        self.setCentralWidget(self.central_widget) 
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        self.os_selection = QComboBox()
        self.os_selection.addItem("Windows")
        self.os_selection.addItem("Mac")
        self.layout.addWidget(self.os_selection)

        self.download_thread = None

    def check_for_updates(self):
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r', encoding='utf-8') as f:
                local_version_str = f.read().strip().strip('\n')
                if not local_version_str:
                    QMessageBox.critical(self, "Error", "Version file is empty")
                    return
                try:
                    local_version = Version(local_version_str)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error reading version file: {e}")
                    return
            try:
                response = requests.get("https://windows.lightwrite.site/Version.txt")
                self.online_version = Version(response.text)
                if self.online_version.is_different_than(local_version):
                    self.status_label.setText("Update found")
                    if os.path.exists(self.version_file):
                        os.remove(self.version_file)
                    build_folder = os.path.join(self.root_path, "Build")
                    if os.path.exists(build_folder):
                        shutil.rmtree(build_folder)
                    self.download_game_files(self.online_version)
                else:
                    self.status_label.setText("Up to date")
                    self.launch_game_if_exists(executable_name="TrenchWars.exe")  # Provide the executable name based on your requirements
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error checking for game updates: {e}")
        else:
            self.download_game_files()

    def download_game_files(self, online_version=None):
        if online_version is None:
            response = requests.get('https://windows.lightwrite.site/Version.txt')
            self.online_version = Version(response.text)

        # Get the selected operating system
        os_selected = self.os_selection.currentText()

        # Download URL based on the selected operating system
        if os_selected == "Windows":
            download_url = 'https://dropbox.com/s/029mx8kwpfwrq9r/Build.zip?dl=1'
            executable_name = "TrenchWars.exe"
        else:  # Assume Mac if not Windows
            download_url = 'https://dropbox.com/s/q0uquyl3qj3mgfw/Build_Mac.zip?dl=1'
            executable_name = "TrenchWars.app"

        # Create the DownloadThread instance here, providing the download_url
        self.download_thread = DownloadThread(download_url)
        self.download_thread.download_progress.connect(self.progress_bar.setValue)
        self.download_thread.download_completed.connect(lambda path: self.on_download_completed(path, executable_name))
        self.download_thread.start()
        self.status_label.setText("Downloading...")

    def on_download_completed(self, file_path, executable_name):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(self.root_path)
        os.remove(file_path)
        with open(self.version_file, 'w') as f:
            f.write(str(self.online_version))
        self.status_label.setText("Done!")
        self.launch_game_if_exists(executable_name)

    def launch_game_if_exists(self, executable_name):
        os_selected = self.os_selection.currentText()
        executable_path = os.path.join(self.root_path, "Build", executable_name)

        if os_selected == "Mac":
            executable_path = os.path.join(executable_path, "Contents", "MacOS", "TrenchWars")

        if os.path.exists(executable_path):
            if os_selected == "Windows":
                os.startfile(executable_path)
            elif os_selected == "Mac":
                os.system(f'open "{executable_path}"')
        else:
            QMessageBox.critical(self, "Error", "Game executable not found")

if __name__ == "__main__":
    app = QApplication([])
    window = LauncherWindow()
    window.show()
    app.exec_()
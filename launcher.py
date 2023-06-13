import os
import requests
import zipfile
import shutil
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Progressbar, Combobox
from threading import Thread

class Version:
    def __init__(self, version_str):
        self.major, self.minor, self.sub_minor = map(int, version_str.split('.'))

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.sub_minor}'

    def is_different_than(self, other):
        return (self.major, self.minor, self.sub_minor) != (other.major, other.minor, other.sub_minor)

class DownloadThread(Thread):
    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url
        self.download_progress = 0

    def run(self):
        response = requests.get(self.download_url, stream=True)
        file_size = int(response.headers.get('Content-Length', 0))
        block_size = 1024
        progress = 0
        with open('Build.zip', 'wb') as out_file:
            for data in response.iter_content(block_size):
                out_file.write(data)
                progress += len(data)
                self.download_progress = int((float(progress) / file_size) * 100)

class LauncherWindow(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.online_version = None
        self.root_path = os.getcwd()
        self.version_file = os.path.join(self.root_path, "Version.txt")
        self.game_zip = os.path.join(self.root_path, "Build.zip")

        self.title("Game Launcher")

        self.play_button = tk.Button(self, text="Check for updates", command=self.check_for_updates)
        self.play_button.pack()

        self.status_label = tk.Label(self, text="")
        self.status_label.pack()

        self.progress_bar = Progressbar(self, mode="determinate")
        self.progress_bar.pack()

        self.os_selection = Combobox(self)
        self.os_selection["values"] = ("Windows", "Mac")
        self.os_selection.current(0)
        self.os_selection.pack()

        self.download_thread = None

    def check_for_updates(self):
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r', encoding='utf-8') as f:
                local_version_str = f.read().strip().strip('\n')
                if not local_version_str:
                    messagebox.showerror("Error", "Version file is empty")
                    return
                try:
                    local_version = Version(local_version_str)
                except Exception as e:
                    messagebox.showerror("Error", f"Error reading version file: {e}")
                    return
            try:
                response = requests.get("https://windows.lightwrite.site/Version.txt")
                self.online_version = Version(response.text)
                if self.online_version.is_different_than(local_version):
                    self.status_label.config(text="Update found")
                    if os.path.exists(self.version_file):
                        os.remove(self.version_file)
                    build_folder = os.path.join(self.root_path, "Build")
                    if os.path.exists(build_folder):
                        shutil.rmtree(build_folder)
                    self.download_game_files(self.online_version)
                else:
                    self.status_label.config(text="Up to date")
                    self.launch_game_if_exists(executable_name="TrenchWars.exe")  # Provide the executable name based on your requirements
            except Exception as e:
                messagebox.showerror("Error", f"Error checking for game updates: {e}")
        else:
            self.download_game_files()

    def download_game_files(self, online_version=None):
        if online_version is None:
            response = requests.get('https://windows.lightwrite.site/Version.txt')
            self.online_version = Version(response.text)

        # Get the selected operating system
        os_selected = self.os_selection.get()

        # Download URL based on the selected operating system
        if os_selected == "Windows":
            download_url = 'https://dropbox.com/s/029mx8kwpfwrq9r/Build.zip?dl=1'
            executable_name = "TrenchWars.exe"
        else:  # Assume Mac if not Windows
            download_url = 'https://dropbox.com/s/q0uquyl3qj3mgfw/Build_Mac.zip?dl=1'
            executable_name = "TrenchWars.app"

        # Create the DownloadThread instance here, providing the download_url
        self.download_thread = DownloadThread(download_url)
        self.progress_bar["maximum"] = 100
        self.progress_bar["value"] = 0
        self.status_label.config(text="Downloading...")
        self.download_thread.start()
        self.check_download_progress(executable_name)

    def check_download_progress(self, executable_name):
        if self.download_thread.is_alive():
            self.progress_bar["value"] = self.download_thread.download_progress
            self.after(100, lambda: self.check_download_progress(executable_name))
        else:
            self.on_download_completed(executable_name)

    def on_download_completed(self, executable_name):
        with zipfile.ZipFile('Build.zip', 'r') as zip_ref:
            zip_ref.extractall(self.root_path)
        os.remove('Build.zip')
        with open(self.version_file, 'w') as f:
            f.write(str(self.online_version))
        self.status_label.config(text="Done!")
        self.launch_game_if_exists(executable_name)

    def launch_game_if_exists(self, executable_name):
        os_selected = self.os_selection.get()
        executable_path = os.path.join(self.root_path, "Build", executable_name)

        if os_selected == "Mac":
            executable_path = os.path.join(self.root_path, "Build_Mac", "TrenchWars.app")

        if os.path.exists(executable_path):
            if os_selected == "Windows":
                os.startfile(executable_path)
            elif os_selected == "Mac":
                os.system(f'open "{executable_path}"')
        else:
            messagebox.showerror("Error", "Game executable not found")

if __name__ == "__main__":
    window = LauncherWindow()
    window.mainloop()
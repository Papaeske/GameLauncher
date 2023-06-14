import os
import subprocess
import requests
import zipfile
import shutil
import time
import math
import tkinter as tk
import tkinter.ttk as ttk
import sv_ttk
import platform
import textwrap
from tkinter import messagebox
from tkinter.ttk import Progressbar, Combobox
from threading import Thread
from PIL import Image, ImageTk

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
        self.download_speed = 0
        self.file_size = 0
        self.download_size = 0
        self.start_time = None

    def run(self):
        response = requests.get(self.download_url, stream=True)
        self.file_size = int(response.headers.get('Content-Length', 0))
        block_size = 1024 * 1024
        progress = 0
        self.start_time = time.time()
        with open('Build.zip', 'wb') as out_file:
            for data in response.iter_content(block_size):
                out_file.write(data)
                progress += len(data)
                self.download_size = progress
                self.download_progress = int((float(progress) / self.file_size) * 100)

                elapsed_time = time.time() - self.start_time
                if elapsed_time > 0:
                    self.download_speed = int(progress / (elapsed_time * 1024 * 1024))  # MB/s


class LauncherWindow(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sv_ttk.set_theme("dark")
        self.iconbitmap("images/Icon.ico")

        self.online_version = None
        self.root_path = os.getcwd()
        self.version_file = os.path.join(self.root_path, "Version.txt")
        self.game_zip = os.path.join(self.root_path, "Build.zip")

        self.title("Launcher")
        self.geometry("400x325")  # Set the window size

        self.install_button = ttk.Button(self, text="Install", command=self.install_game)
        self.install_button.pack(pady=20)

        self.status_label = ttk.Label(self, text="")
        self.status_label.pack()

        self.progress_bar = ttk.Progressbar(self, mode="determinate")
        self.progress_bar.pack(pady=10)

        self.speed_label = ttk.Label(self, text="")
        self.speed_label.pack(pady=5)

        self.size_label = ttk.Label(self, text="")
        self.size_label.pack(pady=5)

        self.time_label = ttk.Label(self, text="")
        self.time_label.pack(pady=5)

        self.os_selection = Combobox(self, state="readonly")
        self.os_selection["values"] = ("Windows", "Mac")
        if platform.system() == "Windows":
            self.os_selection.current(0)
        else:
            self.os_selection.current(1)
        self.os_selection.pack()

        def clear_selection(event):
            event.widget.selection_clear()

        self.os_selection.bind("<FocusIn>", clear_selection)

        self.uninstall_button = ttk.Button(self, text="Uninstall", command=self.uninstall_game)
        self.uninstall_button.pack(pady=20)

        self.image_path = "images/moods.png"  # Replace with the path to your image file
        self.image = Image.open(self.image_path)
        self.image = self.image.resize((100, 43), Image.LANCZOS)
        self.image_tk = ImageTk.PhotoImage(self.image)

        self.image_label = ttk.Label(self, image=self.image_tk)
        self.image_label.place(relx=1, rely=1, anchor="se")

        self.download_thread = None

        self.update_ui()

        self.check_code_update()

    def check_code_update(self):
        github_url = "https://raw.githubusercontent.com/Papaeske/GameLauncher/main/launcher.py"
        response = requests.get(github_url)
        github_code = response.text

        with open(__file__, 'r') as f:
            local_code = f.read()

        if local_code != github_code:
            # Remove extra indentation from the GitHub code
            github_lines = github_code.split('\n')
            min_indent = min(len(line) - len(line.lstrip()) for line in github_lines if line.strip())
            cleaned_lines = [line[min_indent:].rstrip() for line in github_lines]

            # Replace local code with cleaned GitHub code
            cleaned_code = '\n'.join(cleaned_lines)
            with open(__file__, 'w') as f:
                f.write(cleaned_code)

            # Restart the launcher
            messagebox.showinfo("Code Update", "Local code has been updated. Please restart the launcher.")
            self.destroy()

    def update_ui(self):
        game_installed = self.check_game_installed()
        if game_installed:
            self.install_button.configure(text="Check for updates", command=self.check_for_updates)
            self.uninstall_button.pack(pady=20)
        else:
            self.install_button.configure(text="Install", command=self.install_game)
            self.uninstall_button.pack_forget()

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
        self.speed_label.config(text="")
        self.size_label.config(text="")
        self.time_label.config(text="")
        self.download_thread.start()
        self.check_download_progress(executable_name)

    def check_download_progress(self, executable_name):
        if self.download_thread.is_alive():
            self.progress_bar["value"] = self.download_thread.download_progress
            self.speed_label.config(text=f"Download Speed: {self.download_thread.download_speed} MB/s")
            self.size_label.config(text=self.format_size(self.download_thread.download_size, self.download_thread.file_size))
            self.time_label.config(text=f"Estimated Time Remaining: {self.format_time(self.calculate_time_remaining())}")
            self.after(100, lambda: self.check_download_progress(executable_name))
        else:
            self.on_download_completed(executable_name)

    def calculate_time_remaining(self):
        if self.download_thread.download_speed > 0:
            remaining_bytes = self.download_thread.file_size - self.download_thread.download_size
            remaining_time = remaining_bytes / (self.download_thread.download_speed * 1024 * 1024)  # seconds
            if remaining_time > 0:
                return remaining_time
        return float('inf')

    def format_size(self, size_in_bytes, total_size):
        if size_in_bytes < 1024:
            return f"{size_in_bytes} B / {total_size} B"
        elif size_in_bytes < 1024 ** 2:
            return f"{int(size_in_bytes / 1024)} KB / {int(total_size / 1024)} KB"
        elif size_in_bytes < 1024 ** 3:
            return f"{int(size_in_bytes / (1024 ** 2))} MB / {int(total_size / (1024 ** 2))} MB"
        else:
            return f"{int(size_in_bytes / (1024 ** 3))} GB / {int(total_size / (1024 ** 3))} GB"

    def format_time(self, time_in_seconds):
        if not math.isnan(time_in_seconds) and time_in_seconds != float('inf'):
            minutes = int(time_in_seconds // 60)
            seconds = int(time_in_seconds % 60)
            return f"{minutes:02d}:{seconds:02d}"
        else:
            return "N/A"

    def on_download_completed(self, executable_name):
        with zipfile.ZipFile('Build.zip', 'r') as zip_ref:
            zip_ref.extractall(self.root_path)
        os.remove('Build.zip')
        with open(self.version_file, 'w') as f:
            f.write(str(self.online_version))
        self.status_label.config(text="Done, launching game")
        self.progress_bar["value"] = 100
        self.speed_label.config(text="")
        self.size_label.config(text="")
        self.time_label.config(text="")
        self.launch_game_if_exists(executable_name)

        # Update the UI after installing the game
        self.update_ui()

    def launch_game_if_exists(self, executable_name):
        os_selected = self.os_selection.get()
        executable_path = os.path.join(self.root_path, "Build", executable_name)

        if os_selected == "Mac":
            executable_path = os.path.join(self.root_path, "Build_Mac", "TrenchWars.app")

        if os.path.exists(executable_path):
            if os_selected == "Windows":
                os.startfile(executable_path)
            elif os_selected == "Mac":
                subprocess.run(["chmod", "-R", "+x", executable_path])
                os.system(f'open "{executable_path}"')
        else:
            messagebox.showerror("Error", "Game executable not found")

    def install_game(self):
        self.download_game_files()

    def uninstall_game(self):
        if os.path.exists(self.version_file):
            os.remove(self.version_file)
        if os.path.exists(self.game_zip):
            os.remove(self.game_zip)
        if os.path.exists(os.path.join(self.root_path, "Build")):
            shutil.rmtree(os.path.join(self.root_path, "Build"))
        if os.path.exists(os.path.join(self.root_path, "Build_Mac")):
            shutil.rmtree(os.path.join(self.root_path, "Build_Mac"))

        self.status_label.config(text="Game has been removed")

        # Update the UI after uninstalling the game
        self.update_ui()

    def check_game_installed(self):
        executable_name = "TrenchWars.exe" if self.os_selection.get() == "Windows" else "TrenchWars.app"
        executable_path = os.path.join(self.root_path, "Build", executable_name)
        return os.path.exists(executable_path)


if __name__ == "__main__":
    window = LauncherWindow()
    window.mainloop()
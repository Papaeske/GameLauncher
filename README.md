# Launcher Readme

This file contains the code for a launcher application that installs and updates a game. It provides a user interface for downloading the game files, checking for updates, and launching the game.

## Usage

To use the launcher, follow these steps:

1. Ensure that Python is installed on your system.

2. Install the required dependencies. You can install the dependencies using the following command:

   ```
   pip install pillow requests
   ```

3. Run the launcher by executing the following command:

   ```
   python launcher.py
   ```

4. The launcher window will open, displaying a splash screen and various buttons and labels.

5. If the game is already installed, the launcher will display a "Check for updates" button. Clicking this button will check for updates and install them if available.

6. If the game is not installed, the launcher will display an "Install" button. Clicking this button will download and install the game files.

7. During the download process, the launcher will display a progress bar showing the download progress, as well as other information such as download speed, file size, and estimated time remaining.

8. Once the download is complete, the game will be installed, and the launcher will display a "Done, launching game" message.

9. Clicking the "Uninstall" button will remove the game files from your system.

10. The launcher supports multiple operating systems. You can select the desired operating system (Windows or Mac) from a dropdown menu in the launcher window.

## Additional Information

- The launcher uses the `requests` library to download files from the internet.

- The downloaded game files are stored in a zip archive (`Build.zip` or `Build_Mac.zip`), which is extracted to the appropriate location on your system.

- The launcher checks for updates by comparing the local version of the game with the online version specified in a version file (`Version.txt`).

- The launcher supports displaying a splash screen image and an application icon.

- The launcher provides a progress bar to indicate the download progress and other labels to display download speed, file size, and estimated time remaining.

- The launcher uses multi-threading to download the game files, allowing the UI to remain responsive during the download process.

- After the game is installed or updated, the launcher can launch the game by executing the game's executable file (`TrenchWars.exe` or `TrenchWars.app`) if it exists.

- If the game executable is not found, an error message is displayed.

- The launcher checks for updates to its own code by comparing the local code with the code hosted on a specified URL. If an update is found, the launcher code is updated, and a message is displayed asking the user to restart the launcher.

Please note that this is a sample launcher application and may need modifications to work with specific games or environments. Feel free to customize and enhance the code to suit your needs.
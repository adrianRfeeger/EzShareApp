# EzShareCPAP
![image](https://github.com/adrianRfeeger/EzShareCPAP/assets/139186297/2c8f07cc-0bcd-41db-99a9-8050c2dcc037)

## Overview

EzShareCPAP is a macOS program designed to download files from an [ez Share SD card/adapter](https://www.youtube.com/watch?v=ANz8pNDHAPo) when used in CPAP devices (such as the ResMed AirSense 10 Elite) to a local directory. These files can then be imported with applications such as [OSCAR](https://www.sleepfiles.com/OSCAR/) and [SleepHQ](https://home.sleephq.com/) for data analysis and visualisation.

## Features

- **Wi-Fi Connectivity:** Connects to the ez Share SD card's Wi-Fi network.
- **File Synchronisation:** Downloads files from the SD card to a specified local directory.
- **User Interface:** Provides a graphical user interface (GUI) for ease of use.
- **Configuration:** Handles configuration settings directly through the GUI.
- **Real-time Updates:** Displays status updates during the file synchronisation process.
- **Import with OSCAR:** Option to automatically import data with OSCAR after completion.
- **Quit After Completion:** Option to automatically quit the application after completion.

## Prerequisites

- macOS operating system.
- Python 3.x installed on your system (for source installation).
- Required Python packages: `requests`, `beautifulsoup4`, `PyQt6` (for source installation).

## Installation

### From Release Version (mac M series/ARM64/silicon only, for Intel use the source version)

1. **Download the release version:**

   - Download the release version compiled by PyInstaller from [here](https://github.com/adrianrfeeger/EzShareCPAP/releases).

2. **Extract the ZIP file:**

   - Unzip the downloaded file and move to a desired location on your macOS system (e.g., Applications folder).

### From Source

1. **Clone the repository:**

   ```bash
   git clone https://github.com/adrianrfeeger/EzShareCPAP.git
   cd EzShareCPAP
   ```

2. **Install the required packages:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the program:**

   ```bash
   python main.py
   ```

## Compiling Standalone Using PyInstaller

1. **Install PyInstaller:**

   ```bash
   pip install pyinstaller
   ```

2. **Compile the application:**

   ```bash
   pyinstaller EzShareCPAP.spec
   ```

   - This will create a standalone executable in the `dist` folder.

## Usage

### Graphical User Interface (GUI)

The GUI provides an easy way to configure and run the file synchronisation process.

**Path:**  
Specify the local directory where the files will be downloaded.

**URL:**  
Specify the URL of the ez Share SD card.

**Wi-Fi SSID:**  
Specify the SSID of the ez Share Wi-Fi network. The default SSID is `ez Share`.

**Wi-Fi PSK:**  
Specify the PSK (password) for the ez Share Wi-Fi network. The default PSK is `88888888`.

**Checkboxes:**
- **Import with OSCAR after completion:** Automatically imports data into OSCAR after the synchronisation process is completed.
- **Quit after completion:** Automatically quits the application after the synchronisation process is completed.

**Buttons:**
- **Start:** Initiates the synchronisation process.
- **Save Settings:** Saves the current settings to `config.ini`.
- **Restore Defaults:** Restores the default settings.
- **Cancel:** Cancels the current operation.
- **Quit:** Closes the application.

**Progress Bar:**  
Displays the progress of the file synchronisation process.

**Status Label:**  
Displays the current status of the application.

The GUI manages the configuration settings directly, eliminating the need to manually edit the `config.ini` file. Enter your settings in the GUI and click "Save Settings" to store them.

## File Structure

- `README.md`: This file, containing documentation for the project.
- `EzShareCPAP.spec`: PyInstaller specification file for building the standalone application.
- `icon.icns`: Icon file for the macOS application.
- `requirements.txt`: Lists required Python packages for the project.
- `config.ini`: Stores settings.
- `main.py`: Entry point for the program.
- `gui.py`: Handles the graphical user interface and configuration settings.
- `ui_main.py`: Defines the gui styling.
- `ezshare.py`: Manages Wi-Fi connection and file synchronisation.
- `file_ops.py`: Manages file operations, including directory traversal and file downloading.
- `wifi.py`: Handles Wi-Fi connections specific to macOS.

## Troubleshooting

### Wi-Fi Connection Issues:

- Verify the SSID and PSK in the GUI are correct. Default SSID is `ez Share`, and the default PSK is `88888888`.
- Ensure the EzShare SD card/adapter is inserted into a powered-on device (e.g., CPAP) and within range of your computer (5-10 metres).

### File Download Issues:

- Confirm the URL in the GUI points to the correct EzShare SD card address.
- Ensure sufficient space is available in the local directory for file downloads.

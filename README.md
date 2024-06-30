
# EzShareCPAP

## Overview

EzShareCPAP is a macOS program designed to download files from an EzShare SD card used in CPAP devices, such as the ResMed AirSense 10 Elite, to a local directory. These files can be utilised with applications like [OSCAR](https://www.sleepfiles.com/OSCAR/) and [SleepHQ](https://home.sleephq.com/) for data analysis and visualisation.

## Features

- **Wi-Fi Connectivity:** Connects to the EzShare SD card's Wi-Fi network.
- **File Synchronisation:** Downloads files from the SD card to a specified local directory.
- **User Interface:** Provides a graphical user interface (GUI) for ease of use.
- **Configuration:** Handles configuration settings directly through the GUI.
- **Real-time Updates:** Displays status updates during the file synchronisation process.

## Prerequisites

- macOS operating system.
- Python 3.x installed on your system (for source installation).
- Required Python packages: `requests`, `beautifulsoup4`, `PyQt6` (for source installation).

## Installation

### From Source

1. **Clone the repository:**

   \```bash
   git clone https://github.com/adrianrfeeger/EzShareCPAP.git
   cd EzShareCPAP
   \```

2. **Install the required packages:**

   \```bash
   pip install -r requirements.txt
   \```

### From Release Version

1. **Download the release version:**

   - Download the release version compiled by PyInstaller for ARM64 Macs from the [here](https://github.com/adrianRfeeger/EzShareCPAP/releases/download/v1.0.1/EzShareCPAP.zip).

2. **Extract the ZIP file:**

   - Unzip the downloaded file and move to a desired location on your macOS system (ie Applications folder)

## Usage

### Running from Source

1. **Run the program:**

   \```bash
   python main.py
   \```

2. **Using the GUI:**

   - **Path:** Specify the local directory for downloading files. Use the "Browse" button to select the directory.
   - **URL:** Enter the URL of the EzShare SD card, typically `http://192.168.4.1/dir?dir=A:`.
   - **WiFi SSID:** Enter the SSID of the EzShare SD card's Wi-Fi network. The default SSID is `ez Share`.
   - **WiFi PSK:** Enter the pre-shared key (PSK) for the Wi-Fi network. The default PSK is `88888888`.

   **Buttons:**
   - **Start:** Initiates the synchronisation process.
   - **Save Settings:** Saves the current settings to `config.ini`.
   - **Restore Defaults:** Restores the default EzShare Wi-Fi settings.
   - **Cancel:** Cancels the current operation.

   **Progress Bar:** Displays the progress of the file synchronisation process.

   The GUI manages the configuration settings directly, eliminating the need to manually edit the `config.ini` file. Enter your settings in the GUI and click "Save Settings" to store them.

### Running from Release Version


1. **Run the standalone application:**

   - Navigate to where you put EzShareCPAP.app and double-click it.

2. **Using the GUI:**

   - **Path:** Specify the local directory for downloading files. Use the "Browse" button to select the directory.
   - **URL:** Enter the URL of the EzShare SD card, typically `http://192.168.4.1/dir?dir=A:`.
   - **WiFi SSID:** Enter the SSID of the EzShare SD card's Wi-Fi network. The default SSID is `ez Share`.
   - **WiFi PSK:** Enter the pre-shared key (PSK) for the Wi-Fi network. The default PSK is `88888888`.

   **Buttons:**
   - **Start:** Initiates the synchronisation process.
   - **Save Settings:** Saves the current settings to `config.ini`.
   - **Restore Defaults:** Restores the default EzShare Wi-Fi settings.
   - **Cancel:** Cancels the current operation.

   **Progress Bar:** Displays the progress of the file synchronisation process.

   The GUI manages the configuration settings directly, eliminating the need to manually edit the `config.ini` file. Enter your settings in the GUI and click "Save Settings" to store them.

## File Structure

- `main.py`: Entry point for the program.
- `gui.py`: Handles the graphical user interface and configuration settings.
- `ezshare.py`: Manages Wi-Fi connection and file synchronisation.
- `wifi.py`: Handles Wi-Fi connections specific to macOS.
- `file_ops.py`: Manages file operations, including directory traversal and file downloading.
- `config.ini`: Stores Wi-Fi credentials and paths configuration.

## Troubleshooting

- **Wi-Fi Connection Issues:**
  - Verify the SSID and PSK in the GUI are correct. Default SSID is `ez Share`, and the default PSK is `88888888`.
  - Ensure the EzShare SD card is powered on and within range.

- **File Download Issues:**
  - Confirm the URL in the GUI points to the correct EzShare SD card address.
  - Ensure sufficient space is available in the local directory for file downloads.

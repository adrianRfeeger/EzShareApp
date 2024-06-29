# EzShare CPAP Data Downloader for macOS

## Overview

This program downloads files from an EzShare SD card used in CPAP devices like the ResMed AirSense 10 Elite to a local directory on a macOS system. The downloaded files can then be used with programs such as OSCAR and SleepHQ for data analysis and visualization.

## Features

- Connects to the EzShare SD card's Wi-Fi network.
- Downloads files from the SD card to a local directory.
- Provides a graphical user interface for ease of use.
- Handles configuration settings directly through the GUI.
- Displays real-time status updates during the file synchronization process.

## Prerequisites

- macOS operating system.
- Python 3.x installed on your system.
- Required Python packages: `requests`, `beautifulsoup4`, `PyQt6`.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/ezshare-cpap-downloader.git
   cd ezshare-cpap-downloader
   ```

2. **Install the required packages:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the program:**

   ```bash
   python main.py
   ```

2. **Using the GUI:**

   When you launch the program, the graphical user interface (GUI) will appear, as shown below:

   ![GUI Screenshot](./path/to/your/image.png)

   - **Path**: Specify the local directory where the files will be downloaded. You can use the "Browse" button to select the directory.
   - **URL**: Enter the URL of the EzShare SD card. This is typically something like `http://192.168.4.1/dir?dir=A:`.
   - **WiFi SSID**: Enter the SSID of the EzShare SD card's Wi-Fi network. The default SSID is `ez Share`.
   - **WiFi PSK**: Enter the pre-shared key (PSK) for the Wi-Fi network. The default PSK is `88888888`.

   Buttons:
   - **Start**: Initiates the synchronization process.
   - **Save Settings**: Saves the current settings to `config.ini`.
   - **Restore Defaults**: Restores the default settings from `config.ini`.
   - **Cancel**: Cancels the current operation.

   - **Progress Bar**: Displays the progress of the file synchronization process.

   The GUI handles the configuration settings directly, so you don't need to manually edit the `config.ini` file. Simply enter your settings in the GUI and click "Save Settings" to store them.

## File Structure

- `config.ini`: Configuration file for storing Wi-Fi credentials and paths.
- `ezshare.py`: Main functionality for managing Wi-Fi connection and file synchronization.
- `file_ops.py`: Handles file operations such as directory traversal and file downloading.
- `gui.py`: Graphical user interface for the program, which also handles configuration settings.
- `main.py`: Entry point for the program.
- `wifi.py`: Manages Wi-Fi connections specific to macOS.

## Troubleshooting

- **Wi-Fi Connection Issues:**
  - Ensure that the SSID and PSK in the GUI are correct. The default SSID is `ez Share` and the default PSK is `88888888`.
  - Verify that the EzShare SD card is powered on and within range.

- **File Download Issues:**
  - Check the URL in the GUI to ensure it points to the correct address of the EzShare SD card.
  - Verify that there is sufficient space in the local directory for downloading files.

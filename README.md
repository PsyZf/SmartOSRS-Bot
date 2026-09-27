# SmartCrab OSRS

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)

**SmartCrab OSRS** is a next-generation, computer-vision-based automation framework for Old School RuneScape, focusing specifically on Sand Crab training. Built with OpenCV and PyTorch (EasyOCR), it features a highly resilient architecture that does not interact with the game client memory, relying entirely on visual data and humanized I/O.

## Features

- **Modern GUI Launcher**: A sleek, standalone CustomTkinter interface to control the bot, configure hotkeys, and monitor logs.
- **Computer Vision Navigation**: Navigates accurately using color-coded ground markers (via RuneLite).
- **OCR Auto-Recovery**: Uses EasyOCR (PyTorch CPU) to read text on the login/disconnect screens and autonomously recover from 6-hour logs or connection drops.
- **Humanized Macro Recorder**: Includes a built-in macro recording tool that captures physical mouse events and plays them back with Gaussian (randomized) delays and pixel coordinate offsets.
- **Robust Failsafes**: Constantly monitors the HP orb color, combat timers, and screen state. If the bot gets lost or a random interface opens, it instantly auto-calibrates or forces a home-recovery path.
- **Live Screenshot Stream**: The GUI actively displays what the bot is looking at in real-time.

## Installation

### Prerequisites
1. Python 3.12+
2. Tesseract-OCR (optional fallback, EasyOCR is the primary engine)
3. RuneLite (Required for plugins)

### Setup
Clone the repository and install the required dependencies:

```bash
git clone https://github.com/YourUsername/SmartCrab-OSRS.git
cd SmartCrab-OSRS
pip install -r requirements.txt
```
*(Note: To ensure compatibility on all Windows machines without C++ build tools, PyTorch is configured to run in CPU-only mode).*

## Usage

1. Setup your RuneLite client:
   - Layout: `Fixed - Classic Layout`
   - Camera: Fully zoomed out, pitch all the way up.
   - Compass: Facing exactly North.
2. Tag your tiles (Magenta = Home, Cyan = Path, Blue = Far point).
3. Run the Launcher:
   ```bash
   python gui_app.py
   ```
   *(Or double click `OSRS_Smart_Bot_Launcher.exe` if compiled)*
4. Select your configuration in the GUI and hit **START BOT**.

## Hotkeys (Configurable)
- **Pause (`P`)**: Instantly freeze the bot exactly where it is (intercepts active sleeps).
- **Force Home (`W`)**: Abort current pathing and force the bot to seek the Magenta home tile.
- **Stop (`Q`)**: Hard terminate the bot.

## Disclaimer

**Educational Purposes Only.** 
This software was created as an exercise in Computer Vision (OpenCV), OCR integration, and algorithmic mouse humanization. Using automation software ("botting") is strictly against the Jagex Terms of Service and *will* result in your account being banned. 

The authors and contributors of this repository are not responsible for any bans, penalties, or damages incurred from using this software. Use at your own risk.

## License

This project is licensed under the [MIT License](LICENSE).

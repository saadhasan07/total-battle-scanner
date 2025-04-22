# Total Battle Scanner Pro

A powerful scanning tool for Total Battle game that helps detect and analyze resources, player status, and shield status.

## Features

- **Resource Detection**
  - Silver, Ingots, Wood, and Stone detection
  - Configurable minimum thresholds
  - Confidence scoring for detection accuracy

- **Player Status**
  - Online/Offline status detection
  - Shield status detection
  - Shield expiring notification

- **Advanced Scanning**
  - Continuous scanning with configurable delay
  - Multi-resource scanning
  - Sound notifications for valid targets

- **Modern UI**
  - Dark/Light theme support
  - Real-time status updates
  - Scan history tracking
  - Data export functionality

## Requirements

- Python 3.8+
- OpenCV (cv2)
- Tesseract OCR
- PyAutoGUI
- Tkinter
- Additional dependencies in requirements.txt

## Installation

1. Install Python 3.8 or higher
2. Install Tesseract OCR:
   - Windows: Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr`
   - Mac: `brew install tesseract`

3. Install required Python packages:
```bash
pip install -r requirements.txt
```

4. Configure Tesseract path in the script (if different from default)

## Usage

1. Run the application:
```bash
python TotalBattleScanner_FULL.py
```

2. Configure scan settings:
   - Set minimum resource thresholds
   - Choose scan mode (Single resource or All resources)
   - Set scan delay for continuous scanning
   - Enable/disable notifications

3. Start scanning with the "Start Scan" button

## Configuration

- `scanner_settings.json`: Stores user preferences and scan settings
- Template images:
  - `silver_area.png`
  - `ingot_area.png`
  - `wood_area.png`
  - `stone_area.png`
  - `peace_shield_icon.png`
  - `online_status.png`
  - `troop_area.png`

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
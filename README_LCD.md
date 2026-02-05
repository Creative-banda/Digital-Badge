# Face Badge System for LCD Display (Raspberry Pi)

## Overview
This is a modular face recognition badge system designed for Raspberry Pi with a 1.28" LCD display (240x240). It dynamically loads multiple users and displays personalized badges with smooth fade animations when their faces are detected.

## Hardware Requirements
- Raspberry Pi (3/4/Zero 2 W recommended)
- 1.28" Round LCD Display (240x240, SPI interface)
- USB Camera or Pi Camera Module
- MicroSD Card (16GB+ recommended)

## Software Requirements
- Raspberry Pi OS (Bullseye or later)
- Python 3.7+
- LCD library (`lib/LCD_1inch28`)
- OpenCV
- face_recognition library
- Pillow

## Installation

### 1. System Setup on Raspberry Pi

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y libatlas-base-dev libjasper-dev libqtgui4 libqt4-test
sudo apt-get install -y libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev
sudo apt-get install -y libqtgui4 libqt4-test libqtwebkit4

# Install camera dependencies
sudo apt-get install -y libcamera-dev libcamera-apps
sudo apt-get install -y python3-opencv

# Enable SPI for LCD display
sudo raspi-config
# Navigate to: Interface Options -> SPI -> Enable
# Reboot after enabling
```

### 2. Install Python Dependencies

```bash
# Install face_recognition and dependencies
sudo pip3 install face_recognition
sudo pip3 install opencv-python
sudo pip3 install Pillow
sudo pip3 install numpy
```

### 3. Install LCD Library

```bash
# Clone or copy the LCD library to your project
# The library should be in: ../lib/LCD_1inch28
# Make sure the LCD driver is properly installed
```

### 4. Setup Project Structure

```
Badge/
├── main.py                 # Main application
├── known_faces/            # Store face images here
│   ├── ahtesham.jpg
│   ├── john.png
│   └── ...
├── avatars/                # Store avatar images here
│   ├── ahtesham_avatar.jpeg
│   ├── john_avatar.png
│   └── ...
├── lib/                    # LCD library (one level up)
│   └── LCD_1inch28/
└── README_LCD.md           # This file
```

## Usage

### Adding Users

#### 1. Add Face Images
Place clear, front-facing photos in `known_faces/`:
```
known_faces/
  ├── ahtesham.jpg        → Username: "ahtesham"
  ├── john_doe.png        → Username: "john_doe"
  └── sarah.jpeg          → Username: "sarah"
```

#### 2. Add Avatars (Optional)
Place avatars in `avatars/` following the naming pattern:
```
avatars/
  ├── ahtesham_avatar.jpeg    → Matched to "ahtesham"
  ├── john_doe_avatar.png     → Matched to "john_doe"
  └── sarah_avatar.jpg        → Matched to "sarah"
```

**Naming Convention:** `{username}_avatar.{ext}`

### Running the Application

```bash
sudo python3 main.py
```

**Note:** `sudo` is required for SPI access to the LCD display.

### Stopping the Application

Press `Ctrl+C` to stop the application gracefully.

## Features

### Dynamic Multi-User Support
- Automatically scans `known_faces/` folder on startup
- Loads all `.jpg`, `.jpeg`, and `.png` files
- No hardcoding required

### Smart Avatar Matching
- Automatically finds matching avatars using filename patterns
- Supports mixed image formats
- Shows placeholder with initial if no avatar found

### LCD Display Features
- 240x240 round display optimized
- Smooth fade-in/fade-out animations
- Circular avatar masks
- Clean, readable text layout
- Low power consumption

### Face Recognition
- Real-time face detection via camera
- Multiple face database support
- Adjustable tolerance (default: 0.6)
- Fast recognition response

## Display Layout

### Idle Screen
```
┌─────────────────────┐
│                     │
│    Face Badge       │
│      System         │
│       Ready         │
│                     │
└─────────────────────┘
```

### Badge Screen
```
┌─────────────────────┐
│                     │
│      ╭─────╮        │
│      │     │        │ <- Avatar (140x140)
│      │  👤 │        │
│      ╰─────╯        │
│                     │
│    John Doe         │ <- Username
│     Welcome!        │ <- Welcome message
└─────────────────────┘
```

## Troubleshooting

### LCD Display Not Working
```bash
# Check SPI is enabled
ls /dev/spi*
# Should show: /dev/spidev0.0  /dev/spidev0.1

# Test LCD library
cd lib/LCD_1inch28/examples
sudo python3 LCD_1inch28_test.py
```

### Camera Not Detected
```bash
# Check camera connection
vcgencmd get_camera
# Should show: supported=1 detected=1

# Test camera
libcamera-still -o test.jpg

# For USB cameras
ls /dev/video*
```

### Face Recognition Not Working
- Ensure good lighting conditions
- Use clear, front-facing reference photos
- Adjust `tolerance` in code (lower = stricter):
  ```python
  tolerance=0.6  # Default
  tolerance=0.5  # Stricter
  tolerance=0.7  # More lenient
  ```

### Import Errors
```bash
# Verify face_recognition installation
python3 -c "import face_recognition; print('OK')"

# Verify LCD library path
ls ../lib/LCD_1inch28
```

### Performance Issues
- Reduce camera resolution in code
- Increase `time.sleep()` in camera loop
- Use lighter weight face detection model
- Disable unnecessary animations

## Configuration

### Adjust Display Settings

Edit `main.py` to customize:

```python
# Display brightness (0-100)
self.disp.bl_DutyCycle(50)  # 50% brightness

# Fade animation speed
self.fade_image(img, fade_in=True, steps=20, delay=0.02)
# steps: number of frames (higher = smoother but slower)
# delay: time between frames in seconds

# Badge display time
time.sleep(3)  # Show badge for 3 seconds
```

### Adjust Face Recognition

```python
# Recognition tolerance
tolerance=0.6  # Lower = stricter matching

# Camera processing delay
time.sleep(0.1)  # Increase to reduce CPU usage
```

### Font Customization

Change fonts in `create_badge_screen()` and `create_text_screen()`:

```python
font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    20  # Font size
)
```

## Auto-Start on Boot

Create a systemd service:

```bash
# Create service file
sudo nano /etc/systemd/system/facebadge.service
```

Add the following:

```ini
[Unit]
Description=Face Badge System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Badge
ExecStart=/usr/bin/python3 /home/pi/Badge/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable facebadge.service
sudo systemctl start facebadge.service

# Check status
sudo systemctl status facebadge.service

# View logs
sudo journalctl -u facebadge.service -f
```

## Performance Optimization

### For Raspberry Pi Zero
```python
# Reduce face detection frequency
if frame_count % 3 == 0:  # Check every 3rd frame
    face_locations = face_recognition.face_locations(rgb_frame)
```

### For Better Battery Life
```python
# Reduce display brightness
self.disp.bl_DutyCycle(30)  # 30% brightness

# Increase sleep intervals
time.sleep(0.2)  # Instead of 0.1
```

## Tips

1. **Lighting**: Ensure good, consistent lighting for best recognition
2. **Camera Position**: Mount camera at face height, 2-3 feet away
3. **Reference Photos**: Use high-quality, well-lit photos for training
4. **Avatar Size**: Square images (1:1 ratio) work best for avatars
5. **Multiple Angles**: Add multiple photos of same person for better accuracy
6. **Display Rotation**: Adjust `rotate(180)` value if display is upside down

## Technical Specifications

- **Display Resolution**: 240x240 pixels
- **Avatar Size**: 140x140 pixels (circular)
- **Font Sizes**: Title: 24pt, Name: 20pt, Welcome: 16pt
- **Fade Animation**: 20 steps, 0.02s per step (0.4s total)
- **Badge Display Time**: 3 seconds
- **Camera FPS**: ~10 fps (limited by face recognition processing)
- **Recognition Tolerance**: 0.6 (60% similarity threshold)

## License

This project uses:
- face_recognition library (MIT License)
- OpenCV (Apache 2.0 License)
- Pillow (PIL License)

## Credits

- Face recognition powered by `face_recognition` library
- LCD driver based on Waveshare 1.28" LCD examples
- Developed for Raspberry Pi projects

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify hardware connections
3. Check system logs: `sudo journalctl -xe`
4. Test components individually (camera, LCD, face recognition)

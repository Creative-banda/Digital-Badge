#!/bin/bash

# Raspberry Pi Face Recognition Setup Script
echo "Setting up Face Recognition Badge System on Raspberry Pi..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y build-essential cmake pkg-config
sudo apt install -y libopenblas-dev libatlas-base-dev liblapack-dev
sudo apt install -y libhdf5-dev libhdf5-serial-dev libhdf5-103
sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
sudo apt install -y libatlas-base-dev libjasper-dev libqtgui4 libqt4-test
sudo apt install -y libgtk-3-dev libcanberra-gtk-module libcanberra-gtk3-module
sudo apt install -y libjpeg-dev libtiff5-dev libjasper-dev libpng-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install -y libxvidcore-dev libx264-dev libfontconfig1-dev libcairo2-dev
sudo apt install -y libgdk-pixbuf2.0-dev libpango1.0-dev libgtk2.0-dev libgtk-3-dev
sudo apt install -y libboost-all-dev

# Enable camera
echo "Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Create project directory structure
mkdir -p face_badge_system/{known_faces,avatars,ui}
cd face_badge_system

# Create virtual environment
python3 -m venv face_env
source face_env/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel --break-system-packages

# Install packages one by one for better error handling
echo "Installing numpy..."
pip install numpy --break-system-packages

echo "Installing Pillow..."
pip install Pillow --break-system-packages

echo "Installing OpenCV..."
pip install opencv-python --break-system-packages

echo "Installing dlib (this may take 15-20 minutes)..."
pip install dlib --break-system-packages

echo "Installing face-recognition..."
pip install face-recognition --break-system-packages

echo "Setup complete!"
echo "To activate environment: source face_env/bin/activate"
echo "To run: python main.py"
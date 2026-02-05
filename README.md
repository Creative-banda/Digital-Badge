# Face Badge System - User Guide

## Overview
This is a modular face recognition badge system that dynamically loads multiple users and displays personalized badges when their faces are detected.

## Features
- ✨ **Dynamic Multi-User Support**: Automatically loads all faces from the `known_faces/` folder
- 🔄 **Automatic Username Detection**: Extracts usernames from image filenames
- 🎨 **Avatar Matching**: Automatically matches avatars using naming convention
- 📁 **Multiple Format Support**: Supports .jpg, .jpeg, and .png files
- 🎯 **No Manual Configuration**: Just add images and go!

## Setup Instructions

### 1. Add Known Faces
Place face images in the `known_faces/` folder with the following naming pattern:
```
known_faces/
  ├── ahtesham.jpg
  ├── john.png
  ├── sarah.jpeg
  └── ...
```

**Important:** The filename (without extension) will be used as the username.

### 2. Add Avatars (Optional)
Place avatar images in the `avatars/` folder following this naming pattern:
```
avatars/
  ├── ahtesham_avatar.jpeg
  ├── john_avatar.png
  ├── sarah_avatar.jpg
  └── ...
```

**Naming Convention:** `{username}_avatar.{ext}`
- The `{username}` must match the face image filename
- Supported extensions: .jpg, .jpeg, .png (case-insensitive)

### 3. Example Structure
```
known_faces/
  ├── ahtesham.jpg        → Username: "ahtesham"
  └── john_doe.png        → Username: "john_doe"

avatars/
  ├── ahtesham_avatar.jpeg    → Matched to "ahtesham"
  └── john_doe_avatar.png     → Matched to "john_doe"
```

## How It Works

1. **Startup**: The system scans `known_faces/` folder and loads all face images
2. **Face Encoding**: Each face is encoded and stored with its username
3. **Avatar Matching**: For each face, the system looks for a matching avatar
4. **Recognition**: When a face is detected, it's compared against all known faces
5. **Badge Display**: Shows the matched user's avatar and name

## Username Display
- Filenames are converted to display names automatically
- Underscores are replaced with spaces
- Each word is capitalized
- Examples:
  - `ahtesham.jpg` → Display: "Ahtesham"
  - `john_doe.png` → Display: "John Doe"
  - `sarah_smith.jpeg` → Display: "Sarah Smith"

## Adding New Users

### Quick Add (With Avatar):
1. Add face image: `known_faces/username.jpg`
2. Add avatar image: `avatars/username_avatar.jpg`
3. Restart the application

### Quick Add (Without Avatar):
1. Add face image: `known_faces/username.jpg`
2. Restart the application
3. System will show a placeholder circle with the user's initial

## Troubleshooting

### No faces detected
- Ensure the image contains a clear, visible face
- Try using a higher quality image
- Make sure the face is well-lit and front-facing

### Avatar not showing
- Verify the avatar filename follows the pattern: `{username}_avatar.{ext}`
- Check that the username matches exactly (case-sensitive)
- Ensure the file extension is .jpg, .jpeg, or .png

### User not recognized
- Check if the face was loaded successfully (see console output)
- Try adjusting the `tolerance` parameter in the code (default: 0.6)
- Use a better quality reference image

## Console Output
When you run the application, you'll see:
```
Loading 2 face(s) from known_faces...
✓ Loaded: ahtesham (with avatar)
✓ Loaded: john_doe (no avatar found)

Total faces loaded: 2
Recognized users: ahtesham, john_doe
```

## Requirements
- Python 3.7+
- OpenCV
- face_recognition
- Pillow
- tkinter (usually comes with Python)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application
```bash
python main.py
```

Press `ESC` to exit fullscreen mode.

## Technical Details

### Supported Image Formats
- JPEG (.jpg, .jpeg, .JPG, .JPEG)
- PNG (.png, .PNG)

### Face Recognition
- Uses `face_recognition` library
- Default tolerance: 0.6 (lower = stricter matching)
- Processes one face at a time from the camera feed

### Avatar Processing
- Avatars are resized to 200x200 pixels
- Circular mask is applied for aesthetic display
- If no avatar found, shows initial letter in a circle

## Tips
- Use clear, front-facing photos for best recognition accuracy
- Keep avatars square (1:1 aspect ratio) for best results
- File size doesn't matter - images are automatically resized
- You can mix different image formats for faces and avatars

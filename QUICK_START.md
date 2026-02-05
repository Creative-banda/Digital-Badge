# Quick Start Guide - Face Badge System with LCD Display

## System Updated! ✨

Your `main.py` has been updated to work with the 1.28" LCD display instead of tkinter. 

### What Changed:

#### ✅ Removed (Desktop/Tkinter):
- `tkinter` GUI components
- `ImageTk` for image display
- Fullscreen window management
- Mouse/keyboard event handling

#### ✅ Added (Raspberry Pi/LCD):
- LCD_1inch28 display driver integration
- Fade-in/fade-out animations
- Optimized 240x240 display layout
- Direct SPI display control
- Better error handling with logging

### Key Features:

1. **Dynamic User Loading** ✓
   - Automatically loads all faces from `known_faces/`
   - Extracts usernames from filenames (`ahtesham.jpg` → "ahtesham")
   - Matches avatars using `{username}_avatar.{ext}` pattern

2. **LCD Display Optimized** ✓
   - 240x240 resolution
   - Circular avatar masks (140x140)
   - Smooth fade animations
   - Clean text layout

3. **No Manual Configuration** ✓
   - Just drop images in folders
   - System auto-detects everything
   - Supports .jpg, .jpeg, .png

### File Structure:

```
Badge/
├── main.py                      # ← UPDATED FOR LCD!
├── known_faces/
│   ├── ahtesham.jpg            # Your face
│   └── [add more].jpg          # Add more faces here
├── avatars/
│   ├── ahtesham_avatar.jpeg    # Your avatar
│   └── [username]_avatar.jpg   # Pattern: {username}_avatar.{ext}
└── lib/                         # ← LCD library (one dir up)
    └── LCD_1inch28/
```

### To Add New Users:

#### Example: Adding user "john"

1. **Add face image:**
   ```
   known_faces/john.jpg
   ```

2. **Add avatar (optional):**
   ```
   avatars/john_avatar.png
   ```

3. **Restart app** - That's it!

The system will:
- Extract username: `john`
- Display name: `John` (capitalized)
- Show avatar if found, or show "J" in circle

### Running on Raspberry Pi:

```bash
# Make sure you're in the Badge directory
cd /path/to/Badge

# Run with sudo (required for SPI access)
sudo python3 main.py
```

### Expected Output:

```
INFO:root:Loading 1 face(s) from known_faces...
INFO:root:✓ Loaded: ahtesham (with avatar)
INFO:root:Total faces loaded: 1
INFO:root:Recognized users: ahtesham
INFO:root:Camera started, waiting for faces...
```

When a face is detected:
```
INFO:root:Showing badge for: ahtesham
```

### Display Flow:

1. **Idle Screen** (waiting)
   ```
   Face Badge
     System
      Ready
   ```

2. **Face Detected** → Fade out idle

3. **Badge Screen** → Fade in
   ```
   ┌──────────┐
   │   👤    │  ← Avatar (circular)
   │          │
   │ Ahtesham │  ← Name
   │ Welcome! │  ← Message
   └──────────┘
   ```

4. **After 3 seconds** → Fade out → Back to idle

### Troubleshooting:

#### "Cannot open camera"
```bash
# Check camera
vcgencmd get_camera
# Fix: Enable camera in raspi-config
```

#### "Import lib could not be resolved"
```bash
# LCD library should be one directory up
# Structure should be:
# parent_dir/
#   ├── lib/LCD_1inch28/
#   └── Badge/main.py
```

#### Display upside down?
Change this line in `main.py`:
```python
self.disp.ShowImage(frame.rotate(180))
# Try: 0, 90, 180, or 270
```

### Testing Without Hardware (on Windows):

The code won't run on Windows because it requires:
- LCD hardware library (SPI)
- Raspberry Pi GPIO

To test the logic only, you could:
1. Comment out LCD initialization
2. Add mock display methods
3. Test face loading/recognition only

### Next Steps:

1. ✅ Code is ready for Raspberry Pi
2. 📋 Transfer to Raspberry Pi
3. 🔧 Install dependencies (see README_LCD.md)
4. 📸 Add your faces and avatars
5. 🚀 Run and test!

### Files Updated:
- ✅ `main.py` - Complete LCD version
- ✅ `README_LCD.md` - Detailed setup guide
- ✅ `requirements.txt` - Updated with SPI deps

### Need Help?

See full documentation in `README_LCD.md` for:
- Complete Raspberry Pi setup
- Hardware connections
- Performance optimization
- Auto-start on boot
- And more!

---

**Ready to transfer to your Raspberry Pi! 🎉**

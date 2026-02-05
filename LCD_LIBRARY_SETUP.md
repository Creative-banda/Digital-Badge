# LCD Library Setup - Two Easy Options

The code now supports **TWO different folder structures** - choose whichever is easier for you!

---

## ✅ Option 1: Copy `lib` INTO Your Badge Project (RECOMMENDED)

This is the **easiest** option - just copy the library into your project folder.

### Structure:
```
Badge/                          ← Your project folder
├── main.py
├── known_faces/
├── avatars/
└── lib/                        ← Copy LCD library here!
    └── LCD_1inch28/
        ├── __init__.py
        ├── LCD_1inch28.py
        └── ... other files
```

### Steps:
```bash
# Navigate to your Badge project
cd /path/to/Badge

# Copy the LCD library here
cp -r /path/to/waveshare/lib ./lib

# Or if you have the library elsewhere:
cp -r /path/to/LCD_library/lib ./lib
```

### Verification:
```bash
# Check the structure
ls -la lib/LCD_1inch28/

# Should show:
# LCD_1inch28.py
# __init__.py
# etc.
```

### Run:
```bash
sudo python3 main.py
```

**✅ DONE! This works perfectly!**

---

## ✅ Option 2: Keep Library ONE Level Up (Original Method)

Keep the library outside your project folder (one directory up).

### Structure:
```
parent_folder/
├── lib/                        ← LCD library here
│   └── LCD_1inch28/
│       ├── __init__.py
│       ├── LCD_1inch28.py
│       └── ...
└── Badge/                      ← Your project here
    ├── main.py
    ├── known_faces/
    └── avatars/
```

### Steps:
```bash
# The library is already one level up
cd parent_folder
ls lib/LCD_1inch28/  # Verify it's there

cd Badge
sudo python3 main.py
```

**✅ This also works!**

---

## 🎯 Which Option Should You Choose?

### Choose **Option 1** (Copy INTO project) if:
- ✅ You want everything in one folder
- ✅ You want to easily move/copy your entire project
- ✅ You want simpler deployment
- ✅ **RECOMMENDED for most users!**

### Choose **Option 2** (Keep separate) if:
- ✅ You have multiple projects using the same LCD library
- ✅ You want to save disk space (no duplicate libraries)
- ✅ You're following Waveshare's original example structure

---

## 🔧 How the Code Works

The updated `main.py` automatically checks **BOTH locations**:

```python
# Check Option 1: lib in same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check Option 2: lib one level up
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Import will work from either location!
from lib import LCD_1inch28
```

Python will automatically use whichever location has the library! 🎉

---

## 📦 Complete Project Structure (Option 1 - Recommended)

```
Badge/
├── main.py                     # Main application
├── requirements.txt            # Python dependencies
├── README_LCD.md              # Setup guide
├── QUICK_START.md             # Quick reference
├── MIGRATION.md               # Technical details
├── LCD_LIBRARY_SETUP.md       # This file
│
├── lib/                        # LCD library (copy here!)
│   └── LCD_1inch28/
│       ├── __init__.py
│       ├── LCD_1inch28.py
│       └── ... (driver files)
│
├── known_faces/               # Face images
│   ├── ahtesham.jpg
│   ├── john.png
│   └── ...
│
└── avatars/                   # Avatar images (optional)
    ├── ahtesham_avatar.jpeg
    ├── john_avatar.png
    └── ...
```

---

## 🚀 Quick Copy Commands

### If you have Waveshare examples:
```bash
# From Waveshare LCD examples folder
cd /path/to/waveshare/LCD_Module_code/RaspberryPi/python

# Copy to your Badge project
cp -r lib /path/to/Badge/

# Done!
```

### If you downloaded separately:
```bash
# Navigate to your Badge folder
cd /path/to/Badge

# Copy the lib folder here
cp -r /source/path/lib ./

# Verify
ls lib/LCD_1inch28/
```

---

## ✅ Testing the Setup

Run this quick test to verify the library is found:

```bash
cd Badge
sudo python3 -c "from lib import LCD_1inch28; print('✓ LCD library found!')"
```

**Expected output:**
```
✓ LCD library found!
```

**If you get an error:**
```
ModuleNotFoundError: No module named 'lib'
```

Then check:
1. Is `lib/` folder in the right place?
2. Is `LCD_1inch28/` inside `lib/`?
3. Is there an `__init__.py` in `lib/LCD_1inch28/`?

---

## 📁 Where to Get the LCD Library

If you don't have the library yet:

### Option A: From Waveshare GitHub
```bash
git clone https://github.com/waveshare/LCD_Module_Code.git
cd LCD_Module_Code/RaspberryPi/python
cp -r lib /path/to/Badge/
```

### Option B: From Waveshare Wiki
1. Visit: https://www.waveshare.com/wiki/1.28inch_LCD_Module
2. Download the demo code
3. Extract and copy the `lib` folder

### Option C: Manual Installation
```bash
# Install required system packages first
sudo apt-get install python3-spidev python3-rpi.gpio

# Then copy the library files to your project
```

---

## 🎓 Summary

| Aspect | Option 1 (In Project) | Option 2 (One Level Up) |
|--------|----------------------|-------------------------|
| **Structure** | `Badge/lib/` | `parent/lib/` |
| **Portability** | ✅ High (everything together) | ❌ Lower (separated) |
| **Ease of Use** | ✅ Simple | ⚠️ Need to track structure |
| **Disk Space** | Uses more | Saves space |
| **Recommended** | ✅ **YES** | For advanced users |

---

## 💡 Pro Tip

**Copy the library into your project (Option 1)**. This way:
- Your entire project is self-contained
- You can zip and transfer it easily
- No confusion about folder structures
- Works exactly the same!

---

## ⚠️ Important Notes

1. **Both options work perfectly** - the code supports both!
2. **No code changes needed** - automatically detects location
3. **Choose what's easier for you** - there's no performance difference
4. **Stick with one method** - don't mix both (pick one structure)

---

**Recommended: Use Option 1 and copy `lib` into your Badge folder! 🎯**

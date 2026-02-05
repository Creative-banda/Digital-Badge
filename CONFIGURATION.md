# Configuration Guide - Face Detection Settings

## Overview
The Face Badge System now includes advanced stability and anti-flicker mechanisms to prevent false triggers and multiple rapid detections.

---

## 🛡️ Anti-Flicker Features Added

### 1. **Consecutive Frame Detection**
- Requires **3 consecutive frames** with the same face before triggering
- Prevents accidental detections from brief camera glitches
- Ensures stable recognition

### 2. **Recognition Cooldown**
- **5-second cooldown** between recognitions
- Prevents the same person triggering multiple times rapidly
- Gives time for the person to move away

### 3. **State Management**
- Proper state tracking (idle → detecting → showing badge)
- Prevents overlapping badge displays
- Clean transitions between states

---

## ⚙️ Adjustable Settings

### In `main.py` `__init__` method:

```python
# Cooldown mechanism to prevent multiple rapid detections
self.last_recognition_time = 0
self.recognition_cooldown = 5.0  # ← ADJUST THIS: Seconds between recognitions

# Detection stability - require multiple consecutive frames
self.detection_frames = 0
self.frames_required = 3  # ← ADJUST THIS: Number of consecutive frames needed
self.last_detected_name = None
```

---

## 🎯 Recommended Settings

### For High Security / Low False Positives:
```python
self.recognition_cooldown = 10.0  # 10 seconds cooldown
self.frames_required = 5          # Require 5 consecutive frames
tolerance=0.5                     # Stricter face matching
```

### For Quick Response / High Traffic:
```python
self.recognition_cooldown = 3.0   # 3 seconds cooldown
self.frames_required = 2          # Require 2 consecutive frames
tolerance=0.6                     # Standard matching
```

### For Very Stable / Demo Mode:
```python
self.recognition_cooldown = 2.0   # 2 seconds cooldown
self.frames_required = 3          # Require 3 consecutive frames
tolerance=0.6                     # Standard matching
```

### For Testing / Development:
```python
self.recognition_cooldown = 1.0   # 1 second cooldown
self.frames_required = 1          # Single frame (instant)
tolerance=0.7                     # Lenient matching
```

---

## 📊 How It Works

### Detection Flow:

```
1. Camera captures frame
   ↓
2. Check if in cooldown period → YES → Skip, wait
   ↓ NO
3. Detect faces in frame
   ↓
4. Face found? → NO → Reset counter, continue
   ↓ YES
5. Same person as last frame? 
   ↓ YES → Increment counter
   ↓ NO → Reset counter to 1
6. Counter >= frames_required?
   ↓ NO → Continue capturing
   ↓ YES
7. TRIGGER BADGE DISPLAY!
   ↓
8. Set cooldown timer
   ↓
9. Show badge animation
   ↓
10. Return to idle
```

### Example Timeline:

```
Time    Frame   Detection   Counter   Action
0.0s    1       ahtesham    1         Wait...
0.1s    2       ahtesham    2         Wait...
0.2s    3       ahtesham    3         ✓ TRIGGER! Show badge
3.2s    -       -           -         Badge displaying...
6.7s    -       -           -         Return to idle
6.8s    4       ahtesham    1         In cooldown, skip
7.0s    5       ahtesham    1         In cooldown, skip
11.8s   6       ahtesham    1         Cooldown over, counting...
11.9s   7       ahtesham    2         Wait...
12.0s   8       ahtesham    3         ✓ TRIGGER! Show badge again
```

---

## 🐛 Troubleshooting Issues

### Issue: System too slow to respond
**Solution:** Reduce settings
```python
self.recognition_cooldown = 2.0   # Shorter cooldown
self.frames_required = 2          # Fewer frames needed
```

### Issue: Too many false triggers
**Solution:** Increase settings
```python
self.recognition_cooldown = 8.0   # Longer cooldown
self.frames_required = 5          # More frames needed
tolerance=0.5                     # Stricter matching
```

### Issue: Badge shows multiple times rapidly
**Solution:** Increase cooldown
```python
self.recognition_cooldown = 10.0  # Much longer cooldown
```

### Issue: Doesn't detect when standing still
**Solution:** Check frames_required
```python
self.frames_required = 2          # Reduce required frames
```

### Issue: Flickers when no face present
**Cause:** Should be fixed! The counter resets when no face is detected.
**Check:** 
- Is the display code running in the right state?
- Are there leftover threads?

---

## 🔍 Debug Mode

Add this to see what's happening in real-time:

```python
# In camera_loop(), add after face detection:
if face_detected:
    logging.debug(f"Frame {self.detection_frames}/{self.frames_required}: {detected_name}")
else:
    logging.debug("No face detected, counter reset")

# Change logging level to DEBUG:
logging.basicConfig(level=logging.DEBUG)
```

---

## 📈 Performance Considerations

### Frame Processing Time:
- Face detection: ~100-300ms per frame
- With 0.1s sleep: ~10 fps effective rate
- 3 frames required = ~0.3 seconds minimum detection time

### CPU Usage:
```python
# Reduce CPU usage if needed:
time.sleep(0.2)  # Instead of 0.1 - slower but less CPU

# Or process every Nth frame:
if frame_count % 2 == 0:  # Process every 2nd frame
    # ... face detection code ...
```

---

## 🎛️ Advanced Configuration

### Different Cooldowns for Different Users:

```python
# In __init__:
self.user_cooldowns = {
    'ahtesham': 3.0,  # 3 seconds for frequent user
    'john': 10.0,     # 10 seconds for infrequent user
}
self.default_cooldown = 5.0

# In camera_loop(), replace cooldown check:
user_cooldown = self.user_cooldowns.get(detected_name, self.default_cooldown)
if current_time - self.last_recognition_time < user_cooldown:
    time.sleep(0.1)
    continue
```

### Dynamic Adjustment Based on Confidence:

```python
# Get face distance (lower = better match)
face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
best_match_distance = face_distances[match_index]

# Adjust frames required based on confidence
if best_match_distance < 0.4:  # Very confident
    self.frames_required = 2
else:  # Less confident
    self.frames_required = 5
```

---

## 📝 Current Default Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| `recognition_cooldown` | 5.0s | Minimum time between recognitions |
| `frames_required` | 3 | Consecutive frames needed |
| `tolerance` | 0.6 | Face matching strictness |
| `badge_display_time` | 3.0s | How long badge shows |
| `frame_delay` | 0.1s | Sleep between camera reads |

---

## 🎯 Quick Tuning Guide

**Want faster response?**
→ Decrease `frames_required` to 2

**Want to prevent accidental triggers?**
→ Increase `frames_required` to 4-5

**Want to allow re-detection sooner?**
→ Decrease `recognition_cooldown` to 3.0

**Want to prevent spam detection?**
→ Increase `recognition_cooldown` to 8.0-10.0

**Want stricter face matching?**
→ Decrease `tolerance` to 0.5

**Want more lenient matching?**
→ Increase `tolerance` to 0.65-0.7

---

## 🚀 Recommended Production Settings

For a badge system at an office/event:

```python
# Balanced settings
self.recognition_cooldown = 5.0   # Allow same person every 5 seconds
self.frames_required = 3          # Require 3 stable frames
tolerance=0.6                     # Standard face matching
```

This provides:
- ✅ Fast enough response (~0.3s detection time)
- ✅ Prevents accidental triggers
- ✅ Smooth, non-flickering display
- ✅ Reasonable cooldown for normal use

---

**All settings can be adjusted without changing core logic!** 🎉

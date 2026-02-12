#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sys
import cv2
import face_recognition
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance, ImageFont
import numpy as np
import os
import time
import glob
import logging
import random
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv
import threading
import json

# Load environment variables from .env file
load_dotenv()

# Add multiple possible paths for LCD library
# Option 1: lib folder in same directory as this script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Option 2: lib folder one level up (original structure)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from lib import LCD_1inch28

logging.basicConfig(level=logging.INFO)

LCD_SIZE = 240

# ============================================
# PERFORMANCE CONFIGURATION
# ============================================
# Adjust these values to balance animation smoothness vs face detection responsiveness
DETECT_EVERY_N_FRAMES = 30      # Check for faces every N frames (higher = smoother animation, slower detection)
                                # At 26 FPS: 30 frames = ~1.2 second detection delay
CAMERA_SCALE = 0.5              # Scale camera frames before detection (0.5 = half size, 4x faster)
FACE_DETECTION_MODEL = "hog"    # "hog" = fast but less accurate, "cnn" = slow but very accurate
FRAMES_REQUIRED_FOR_MATCH = 3   # Consecutive frames needed to confirm face (stability)
FACE_MATCH_TOLERANCE = 0.5      # Lower = stricter matching (0.6 default, 0.5 recommended, 0.4 very strict)

# Google Sheets Integration (loaded from .env file)
ENABLE_GOOGLE_SHEETS = os.getenv("ENABLE_GOOGLE_SHEETS", "True").lower() == "true"
GOOGLE_APPS_SCRIPT_URL = os.getenv("GOOGLE_APPS_SCRIPT_URL", "")

# Backup/Fallback Configuration
BACKUP_DIR = "failed_uploads"   # Directory to store failed uploads
BACKUP_JSON = "failed_uploads/pending_uploads.json"  # JSON file tracking failed uploads

# Validate Google Sheets configuration
if ENABLE_GOOGLE_SHEETS and not GOOGLE_APPS_SCRIPT_URL:
    logging.warning("⚠️  ENABLE_GOOGLE_SHEETS is True but GOOGLE_APPS_SCRIPT_URL is not set in .env file!")
    logging.warning("⚠️  Google Sheets logging will be disabled. Please create a .env file (see .env.example)")
    ENABLE_GOOGLE_SHEETS = False
# ============================================

# Funny messages for unknown faces (randomly selected)
UNKNOWN_FACE_MESSAGES = [
    "Nice try, stranger! 😎\nBut I only know cool people.",
    "Hmm... Do I know you? 🤔\nNope! Access Denied!",
    "Error 404:\nFace Not Found! 😅",
    "Sorry, you're not on\nthe VIP list! 🎭",
    "Who dis? 👀\nNew phone, who dis?",
    "Unauthorized Human\nDetected! 🚫😄",
    "My database says:\n'Never seen this face!' 🤷",
    "Plot twist:\nYou're not in my contacts! 📱"
]


class FaceBadgeSystem:
    def __init__(self):
        # Initialize LCD display
        self.disp = LCD_1inch28.LCD_1inch28()
        self.disp.Init()
        self.disp.clear()
        self.disp.bl_DutyCycle(50)
        
        # Load animation frames
        self.idle_frames = self.load_animation_frames("animations/idle")
        self.scan_frames = self.load_animation_frames("animations/scan")
        
        # Store multiple known faces and their data
        self.known_face_encodings = []
        self.known_face_names = []
        self.avatar_paths = {}
        self.known_face_image_paths = {}  # Store original known face image paths
        self.load_known_faces()
        
        # Store latest camera frame for Google Sheets upload
        self.latest_frame = None
        
        # Login/Logout tracking
        self.user_login_times = {}  # {username: datetime object}
        self.user_login_status = {}  # {username: "logged_in" or "logged_out"}
        self.login_timeout_hours = 1  # Hours before auto-logout
        
        # Create backup directory for failed uploads
        if ENABLE_GOOGLE_SHEETS and not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            logging.info(f"Created backup directory: {BACKUP_DIR}")
        
        # Initialize camera ONCE here
        logging.info("Initializing camera...")
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logging.error("Cannot open camera! Please check camera connection.")
            self.cleanup()
            raise RuntimeError("Camera initialization failed")
        else:
            logging.info("Camera initialized successfully")
        
        # UI state
        self.current_state = "idle"
        self.running = True
        
        # Detection stability - require multiple consecutive frames
        self.detection_frames = 0
        self.frames_required = FRAMES_REQUIRED_FOR_MATCH
        self.last_detected_name = None
        
        logging.info(f"Performance config: detect_interval={DETECT_EVERY_N_FRAMES}, camera_scale={CAMERA_SCALE}, model={FACE_DETECTION_MODEL}")
    
    def load_animation_frames(self, folder_path):
        """Load and resize animation frames from folder"""
        if not os.path.exists(folder_path):
            logging.warning(f"Animation folder not found: {folder_path}")
            return []
        
        # Get all jpg files sorted
        frame_files = sorted(glob.glob(os.path.join(folder_path, "*.jpg")))
        if not frame_files:
            logging.warning(f"No frames found in {folder_path}")
            return []
        
        frames = []
        for frame_file in frame_files:
            try:
                img = Image.open(frame_file).convert("RGB")
                # Resize from 500x500 to 240x240
                img = img.resize((LCD_SIZE, LCD_SIZE), Image.LANCZOS)
                # PRE-ROTATE frames to avoid rotation on every display call
                img = img.rotate(180)
                frames.append(img)
            except Exception as e:
                logging.error(f"Failed to load frame {frame_file}: {e}")
        
        logging.info(f"Loaded {len(frames)} frames from {folder_path}")
        return frames
    
    def load_known_faces(self):
        """Load and encode all known faces from known_faces folder"""
        known_faces_dir = "known_faces"
        
        if not os.path.exists(known_faces_dir):
            logging.warning(f"{known_faces_dir} directory not found")
            return
        
        # Supported image extensions
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        face_files = []
        
        # Get all image files
        for ext in extensions:
            face_files.extend(glob.glob(os.path.join(known_faces_dir, ext)))
        
        if not face_files:
            logging.warning(f"No face images found in {known_faces_dir}")
            return
        
        logging.info(f"Loading {len(face_files)} face(s) from {known_faces_dir}...")
        
        for face_file in face_files:
            try:
                # Extract username from filename (without extension)
                filename = os.path.basename(face_file)
                username = os.path.splitext(filename)[0]
                
                # Load and encode the face
                image = face_recognition.load_image_file(face_file)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_names.append(username)
                    
                    # Store the original known face image path
                    self.known_face_image_paths[username] = face_file
                    
                    # Find matching avatar
                    avatar_path = self.find_avatar(username)
                    if avatar_path:
                        self.avatar_paths[username] = avatar_path
                        logging.info(f"✓ Loaded: {username} (with avatar)")
                    else:
                        logging.info(f"✓ Loaded: {username} (no avatar found)")
                else:
                    logging.warning(f"✗ No face detected in {filename}")
                    
            except Exception as e:
                logging.error(f"✗ Error loading {face_file}: {str(e)}")
        
        logging.info(f"Total faces loaded: {len(self.known_face_names)}")
        if self.known_face_names:
            logging.info(f"Recognized users: {', '.join(self.known_face_names)}")
    
    def find_avatar(self, username):
        """Find avatar image for a given username"""
        avatars_dir = "avatars"
        
        if not os.path.exists(avatars_dir):
            return None
        
        # Look for avatar with pattern: username_avatar.ext
        avatar_pattern = f"{username}_avatar"
        extensions = ['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG']
        
        for ext in extensions:
            avatar_path = os.path.join(avatars_dir, f"{avatar_pattern}.{ext}")
            if os.path.exists(avatar_path):
                return avatar_path
        
        return None
    
    def encode_image_to_base64(self, image_path):
        """Encode image file to base64 string for Google Sheets upload"""
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            logging.error(f"Failed to encode image {image_path}: {e}")
            return None
    
    def save_frame_to_temp(self, frame, username):
        """Save current camera frame to temporary file and return path"""
        try:
            temp_dir = "temp_captures"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(temp_dir, f"{username}_{timestamp}.jpg")
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            pil_img.save(temp_path, "JPEG", quality=85)
            
            return temp_path
        except Exception as e:
            logging.error(f"Failed to save frame: {e}")
            return None
    
    def save_failed_upload(self, username, current_time, current_image_path, known_face_path, error_msg, action="login"):
        """Save failed upload data locally for later retry"""
        try:
            # Create permanent backup directory structure
            backup_images_dir = os.path.join(BACKUP_DIR, "images")
            if not os.path.exists(backup_images_dir):
                os.makedirs(backup_images_dir)
            
            # Copy images to backup directory with timestamp
            timestamp_safe = current_time.replace(":", "-").replace(" ", "_")
            
            # Copy current capture
            backup_current_path = os.path.join(backup_images_dir, f"{username}_{timestamp_safe}_current.jpg")
            import shutil
            shutil.copy2(current_image_path, backup_current_path)
            
            # Copy known face image
            backup_known_path = os.path.join(backup_images_dir, f"{username}_{timestamp_safe}_known.jpg")
            shutil.copy2(known_face_path, backup_known_path)
            
            # Create entry for JSON
            failed_entry = {
                "action": action,  # "login" or "logout"
                "name": username,
                "time": current_time,
                "timestamp": datetime.now().isoformat(),
                "current_image_path": backup_current_path if action == "login" else None,
                "known_face_path": backup_known_path if action == "login" else None,
                "error": error_msg,
                "status": "pending"
            }
            
            # Load existing failed uploads or create new list
            failed_uploads = []
            if os.path.exists(BACKUP_JSON):
                try:
                    with open(BACKUP_JSON, 'r') as f:
                        failed_uploads = json.load(f)
                except:
                    failed_uploads = []
            
            # Add new failed upload
            failed_uploads.append(failed_entry)
            
            # Save to JSON
            with open(BACKUP_JSON, 'w') as f:
                json.dump(failed_uploads, f, indent=2)
            
            logging.info(f"💾 Saved failed upload locally: {username} at {current_time} (action: {action})")
            logging.info(f"📁 Backup location: {BACKUP_DIR}")
            
        except Exception as e:
            logging.error(f"Failed to save backup data: {e}")
    
    def upload_to_google_sheets(self, username, current_frame):
        """Upload attendance data to Google Sheets in background thread"""
        if not ENABLE_GOOGLE_SHEETS:
            return
        
        current_time = datetime.now()
        user_status = self.user_login_status.get(username, None)
        action = None
        
        # Determine what action to take
        if user_status == "logged_out":
            # User already logged out - don't send any request
            logging.info(f"ℹ️  {username} is already logged out - no request sent")
            return
        
        elif user_status == "logged_in":
            # User is logged in - check if timeout reached
            last_login = self.user_login_times[username]
            time_diff = current_time - last_login
            hours_diff = time_diff.total_seconds() / 3600
            
            if hours_diff >= self.login_timeout_hours:
                # Time to logout
                action = "logout"
                self.user_login_status[username] = "logged_out"
                logging.info(f"⏱️  {username} last login was {hours_diff:.1f}h ago - triggering LOGOUT")
            else:
                # Still within timeout - just show badge, no request
                logging.info(f"ℹ️  {username} already logged in ({hours_diff*60:.0f}min ago) - no request sent")
                return
        
        else:
            # First time or no status - LOGIN
            action = "login"
            self.user_login_times[username] = current_time
            self.user_login_status[username] = "logged_in"
            logging.info(f"🆕 First detection for {username} - triggering LOGIN")
        
        # Start upload in background thread
        upload_thread = threading.Thread(
            target=self._upload_worker,
            args=(username, current_frame.copy(), action),
            daemon=True
        )
        upload_thread.start()
        logging.info(f"📤 Started background upload for {username} (action: {action})")
    
    def _upload_worker(self, username, current_frame, action="login"):
        """Background worker thread for Google Sheets upload"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_timestamp_iso = datetime.now().isoformat()
        temp_frame_path = None
        known_face_path = None
        
        try:
            if action == "logout":
                # Send LOGOUT only (no images needed)
                self._send_logout(username, current_timestamp_iso)
                
            elif action == "login":
                # Send LOGIN with images
                # Save current frame to temporary file
                temp_frame_path = self.save_frame_to_temp(current_frame, username)
                if not temp_frame_path:
                    logging.error("Failed to save current frame")
                    return
                
                # Get known face image path
                known_face_path = self.known_face_image_paths.get(username)
                if not known_face_path:
                    logging.error(f"No known face image found for {username}")
                    return
                
                # Encode both images to base64 with data URI prefix
                current_image_b64 = self._encode_image_with_prefix(temp_frame_path)
                known_face_b64 = self._encode_image_with_prefix(known_face_path)
                
                if not current_image_b64 or not known_face_b64:
                    logging.error("Failed to encode images")
                    return
                
                # Prepare data for Google Sheets (LOGIN)
                data = {
                    "action": "login",
                    "name": username,
                    "time": current_timestamp_iso,
                    "user_current_image": current_image_b64,
                    "user_badge_image": known_face_b64
                }
                
                # Send to Google Apps Script
                logging.info(f"🔄 Uploading LOGIN for {username} to Google Sheets...")
                response = requests.post(GOOGLE_APPS_SCRIPT_URL, json=data, timeout=30)
                
                if response.status_code == 200:
                    logging.info(f"✅ Successfully uploaded LOGIN: {username} at {current_time}")
                    # Clean up temporary file on success
                    try:
                        os.remove(temp_frame_path)
                    except:
                        pass
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                    logging.error(f"❌ Failed to upload: {error_msg}")
                    # Save failed upload locally
                    self.save_failed_upload(username, current_time, temp_frame_path, known_face_path, error_msg, action)
                    
        except requests.exceptions.Timeout:
            error_msg = "Request timeout (30s)"
            logging.error(f"⏱️  Google Sheets upload timed out (background thread)")
            # Save failed upload locally
            if action == "login" and temp_frame_path and known_face_path:
                self.save_failed_upload(username, current_time, temp_frame_path, known_face_path, error_msg, action)
                
        except Exception as e:
            error_msg = str(e)
            logging.error(f"❌ Error uploading to Google Sheets (background thread): {e}")
            # Save failed upload locally
            if action == "login" and temp_frame_path and known_face_path:
                self.save_failed_upload(username, current_time, temp_frame_path, known_face_path, error_msg, action)
    
    def _send_logout(self, username, timestamp_iso):
        """Send logout action to Google Sheets"""
        try:
            data = {
                "action": "logout",
                "name": username,
                "time": timestamp_iso
            }
            
            logging.info(f"🔄 Sending LOGOUT for {username} to Google Sheets...")
            response = requests.post(GOOGLE_APPS_SCRIPT_URL, json=data, timeout=30)
            
            if response.status_code == 200:
                logging.info(f"✅ Successfully sent LOGOUT: {username}")
            else:
                logging.error(f"❌ Failed to send LOGOUT: HTTP {response.status_code}")
                
        except Exception as e:
            logging.error(f"❌ Error sending LOGOUT: {e}")
    
    def _encode_image_with_prefix(self, image_path):
        """Encode image to base64 with data URI prefix"""
        try:
            with open(image_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                return f"data:image/jpeg;base64,{encoded}"
        except Exception as e:
            logging.error(f"Failed to encode image {image_path}: {e}")
            return None
    
    def fade_image(self, img, fade_in=True, steps=10, delay=0):
        """Fade in/out an image on the LCD display - NO DELAY for max speed"""
        black = Image.new("RGB", (LCD_SIZE, LCD_SIZE), (0, 0, 0))
        
        for i in range(steps + 1):
            alpha = i / steps if fade_in else 1 - (i / steps)
            frame = Image.blend(black, img, alpha)
            # Badge images need rotation (not pre-rotated)
            self.disp.ShowImage(frame.rotate(180))
            if delay > 0:
                time.sleep(delay)
    
    def create_text_screen(self, text, font_size=24):
        """Create an image with centered text"""
        img = Image.new("RGB", (LCD_SIZE, LCD_SIZE), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                font_size
            )
        except:
            # Fallback to default font if system font not available
            font = ImageFont.load_default()
        
        # Handle multi-line text
        lines = text.split('\n')
        y_offset = LCD_SIZE // 2 - (len(lines) * font_size) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = (LCD_SIZE - tw) // 2
            draw.text((x, y_offset), line, fill=(255, 255, 255), font=font)
            y_offset += font_size + 5
        
        return img
    
    def create_badge_screen(self, username, avatar_path=None, message="Welcome!"):
        """Create badge screen with avatar and name"""
        img = Image.new("RGB", (LCD_SIZE, LCD_SIZE), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if avatar_path and os.path.exists(avatar_path):
            # Use avatar image
            avatar_img = Image.open(avatar_path).convert("RGB")
            
            # Crop to square
            w, h = avatar_img.size
            s = min(w, h)
            avatar_img = avatar_img.crop(((w - s)//2, (h - s)//2, (w + s)//2, (h + s)//2))
            
            # Resize
            avatar_size = 140
            avatar_img = avatar_img.resize((avatar_size, avatar_size), Image.LANCZOS)
            
            # Create circular mask
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            
            # Apply mask
            avatar_img.putalpha(mask)
            
            # Paste avatar
            pos = ((LCD_SIZE - avatar_size) // 2, 30)
            img.paste(avatar_img, pos, avatar_img)
        else:
            # Create placeholder circle with initial
            avatar_size = 140
            x = LCD_SIZE // 2
            y = 100
            draw.ellipse(
                (x - avatar_size//2, y - avatar_size//2, 
                 x + avatar_size//2, y + avatar_size//2),
                fill=(60, 60, 60), outline=(255, 255, 255), width=3
            )
            
            # Draw initial
            initial = username[0].upper() if username else "?"
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    60
                )
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), initial, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((x - tw//2, y - th//2), initial, fill=(255, 255, 255), font=font)
        
        # Draw username
        display_name = username.replace('_', ' ').title()
        try:
            name_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                20
            )
        except:
            name_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), display_name, font=name_font)
        tw = bbox[2] - bbox[0]
        draw.text(((LCD_SIZE - tw) // 2, 185), display_name, fill=(255, 255, 255), font=name_font)
        
        # Draw "Welcome" text (or custom message)
        try:
            welcome_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                16
            )
        except:
            welcome_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), message, font=welcome_font)
        tw = bbox[2] - bbox[0]
        draw.text(((LCD_SIZE - tw) // 2, 210), message, fill=(100, 255, 100), font=welcome_font)
        
        return img
    
    def create_rejection_screen(self, message):
        """Create a funny rejection screen for unknown faces"""
        img = Image.new("RGB", (LCD_SIZE, LCD_SIZE), (20, 20, 40))  # Dark blue background
        draw = ImageDraw.Draw(img)
        
        # Draw big warning icon (circle with X)
        icon_size = 80
        x = LCD_SIZE // 2
        y = 60
        
        # Red circle
        draw.ellipse(
            (x - icon_size//2, y - icon_size//2, 
             x + icon_size//2, y + icon_size//2),
            fill=(200, 50, 50), outline=(255, 100, 100), width=3
        )
        
        # White X
        offset = icon_size // 3
        draw.line(
            (x - offset, y - offset, x + offset, y + offset),
            fill=(255, 255, 255), width=6
        )
        draw.line(
            (x - offset, y + offset, x + offset, y - offset),
            fill=(255, 255, 255), width=6
        )
        
        # Draw funny message
        try:
            msg_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                16
            )
        except:
            msg_font = ImageFont.load_default()
        
        # Split message into lines
        lines = message.split('\n')
        y_offset = 130
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=msg_font)
            tw = bbox[2] - bbox[0]
            draw.text(
                ((LCD_SIZE - tw) // 2, y_offset), 
                line, 
                fill=(255, 220, 100),  # Yellow text
                font=msg_font
            )
            y_offset += 22
        
        return img
    
    def show_idle_screen(self):
        """Display idle screen"""
        idle_img = self.create_text_screen("Face Badge\nSystem\nReady", font_size=24)
        self.disp.ShowImage(idle_img.rotate(180))
        self.current_state = "idle"
    
    def detect_and_show_badge(self):
        """Main loop: idle animation -> detect face -> scan animation -> show badge -> repeat"""
        if not self.cap or not self.cap.isOpened():
            logging.error("Camera not available")
            return
        
        logging.info("Starting face detection...")
        
        idle_frame_idx = 0
        scan_frame_idx = 0
        idle_delay = 0  # NO DELAY - max speed!
        scan_delay = 0  # NO DELAY - max speed!
        detect_every_n_frames = DETECT_EVERY_N_FRAMES
        frame_counter = 0
        
        # Performance monitoring
        fps_counter = 0
        fps_start_time = time.time()
        last_log_time = time.time()
        
        logging.info(f"Detection interval: every {detect_every_n_frames} frames (~{detect_every_n_frames/26:.1f}s at 26fps)")
        
        while self.running:
            # Reset detection state
            self.detection_frames = 0
            self.last_detected_name = None
            self.current_state = "idle"
            
            # IDLE STATE: Play idle animation while waiting for face
            while self.running:
                # Show next idle frame if available
                if self.idle_frames:
                    self.disp.ShowImage(self.idle_frames[idle_frame_idx])  # Already rotated!
                    idle_frame_idx = (idle_frame_idx + 1) % len(self.idle_frames)
                
                frame_counter += 1
                fps_counter += 1
                
                # Log FPS every 2 seconds
                current_time = time.time()
                if current_time - last_log_time > 2.0:
                    elapsed = current_time - fps_start_time
                    current_fps = fps_counter / elapsed if elapsed > 0 else 0
                    logging.info(f"IDLE Animation FPS: {current_fps:.1f}")
                    fps_counter = 0
                    fps_start_time = current_time
                    last_log_time = current_time
                
                # Only check for face every N frames to keep animation smooth
                if frame_counter % detect_every_n_frames == 0:
                    detect_start = time.time()
                    ret, frame = self.cap.read()
                    if ret:
                        # Store latest frame for potential Google Sheets upload
                        self.latest_frame = frame.copy()
                        
                        # Resize camera frame for faster processing
                        small_frame = cv2.resize(frame, (0, 0), fx=CAMERA_SCALE, fy=CAMERA_SCALE)
                        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                        # Use faster HOG model instead of CNN
                        face_locations = face_recognition.face_locations(rgb_frame, model=FACE_DETECTION_MODEL)
                        detect_time = (time.time() - detect_start) * 1000
                        
                        if face_locations and len(self.known_face_encodings) > 0:
                            logging.info(f"Face detected! Detection took: {detect_time:.0f}ms")
                            # Face detected! Switch to SCAN state
                            self.current_state = "scan"
                            scan_frame_idx = 0
                            frame_counter = 0
                            fps_counter = 0
                            fps_start_time = time.time()
                            break
                
                if idle_delay > 0:
                    time.sleep(idle_delay)
            
            # SCAN STATE: Play scan animation while recognizing
            recognized_user = None
            
            while self.running and self.current_state == "scan":
                # Show next scan frame if available
                if self.scan_frames:
                    self.disp.ShowImage(self.scan_frames[scan_frame_idx])  # Already rotated!
                    scan_frame_idx = (scan_frame_idx + 1) % len(self.scan_frames)
                
                frame_counter += 1
                fps_counter += 1
                
                # Log FPS every 2 seconds
                current_time = time.time()
                if current_time - last_log_time > 2.0:
                    elapsed = current_time - fps_start_time
                    current_fps = fps_counter / elapsed if elapsed > 0 else 0
                    logging.info(f"SCAN Animation FPS: {current_fps:.1f}")
                    fps_counter = 0
                    fps_start_time = current_time
                    last_log_time = current_time
                
                # Check face recognition every N frames
                if frame_counter % detect_every_n_frames == 0:
                    recognition_start = time.time()
                    ret, frame = self.cap.read()
                    if not ret:
                        if scan_delay > 0:
                            time.sleep(scan_delay)
                        continue
                    
                    # Store latest frame for potential Google Sheets upload
                    self.latest_frame = frame.copy()
                    
                    # Resize for faster processing
                    small_frame = cv2.resize(frame, (0, 0), fx=CAMERA_SCALE, fy=CAMERA_SCALE)
                    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    # Use faster HOG model instead of CNN
                    face_locations = face_recognition.face_locations(rgb_frame, model=FACE_DETECTION_MODEL)
                    recognition_time = (time.time() - recognition_start) * 1000
                    
                    if not face_locations:
                        # Face lost, only break if we haven't recognized anyone yet
                        if recognized_user is None:
                            self.detection_frames = 0
                            self.last_detected_name = None
                            frame_counter = 0
                            break
                    else:
                        # Encode and match faces
                        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                        
                        face_detected = False
                        detected_name = None
                        
                        for face_encoding in face_encodings:
                            matches = face_recognition.compare_faces(
                                self.known_face_encodings,
                                face_encoding,
                                tolerance=FACE_MATCH_TOLERANCE
                            )
                            
                            if True in matches:
                                # Get face distances to find best match
                                face_distances = face_recognition.face_distance(
                                    self.known_face_encodings, 
                                    face_encoding
                                )
                                best_match_index = np.argmin(face_distances)
                                
                                # Only accept if it's a good match
                                if matches[best_match_index] and face_distances[best_match_index] < FACE_MATCH_TOLERANCE:
                                    detected_name = self.known_face_names[best_match_index]
                                    face_detected = True
                                    logging.info(f"Match confidence: {1 - face_distances[best_match_index]:.2f}")
                                    break
                        
                        if face_detected:
                            if detected_name == self.last_detected_name:
                                self.detection_frames += 1
                            else:
                                self.detection_frames = 1
                                self.last_detected_name = detected_name
                            
                            # Stable recognition achieved!
                            if self.detection_frames >= self.frames_required and recognized_user is None:
                                logging.info(f"Face recognized: {detected_name} (took {recognition_time:.0f}ms)")
                                recognized_user = detected_name
                                # Continue playing animation, don't break yet
                        else:
                            # Face present but NOT RECOGNIZED - check if we've seen unknown face enough times
                            if self.last_detected_name != "UNKNOWN":
                                self.last_detected_name = "UNKNOWN"
                                self.detection_frames = 1
                            else:
                                self.detection_frames += 1
                            
                            # Show funny message for unknown face after stable detection
                            if self.detection_frames >= self.frames_required and recognized_user is None:
                                logging.info(f"Unknown face detected (took {recognition_time:.0f}ms)")
                                recognized_user = "UNKNOWN"
                                # Continue animation, will show rejection message
                
                # Check if scan animation completed one full loop after recognition
                if recognized_user is not None and scan_frame_idx == 0 and frame_counter > detect_every_n_frames:
                    # Scan animation loop complete, show badge
                    self.show_badge(recognized_user)
                    frame_counter = 0
                    break
                
                if scan_delay > 0:
                    time.sleep(scan_delay)
        
        logging.info("Detection stopped")
    
    def show_badge(self, username):
        """Display user badge with animation"""
        self.current_state = "badge"
        
        # Check user status
        user_status = self.user_login_status.get(username, None)
        badge_message = "Welcome!"
        
        if user_status == "logged_out":
            badge_message = "Logged out!\nSee you later! 👋"
            logging.info(f"Showing badge for: {username} (LOGGED OUT - no request)")
        elif user_status == "logged_in":
            # Check if it's time to logout
            last_login = self.user_login_times.get(username)
            if last_login:
                time_diff = datetime.now() - last_login
                hours_diff = time_diff.total_seconds() / 3600
                
                if hours_diff >= self.login_timeout_hours:
                    badge_message = "Logging out...\nSee you soon! 👋"
                    logging.info(f"Showing badge for: {username} (LOGOUT TRIGGERED)")
                else:
                    logging.info(f"Showing badge for: {username} (ALREADY LOGGED IN - no request)")
            else:
                logging.info(f"Showing badge for: {username} (LOGGED IN)")
        else:
            logging.info(f"Showing badge for: {username} (NEW LOGIN)")
        
        # Check if unknown face
        if username == "UNKNOWN":
            # Show funny rejection message
            funny_msg = random.choice(UNKNOWN_FACE_MESSAGES)
            badge_img = self.create_rejection_screen(funny_msg)
            
            # Fade in
            self.fade_image(badge_img, fade_in=True, steps=10, delay=0)
            
            # Display for 3 seconds (longer so they can read the joke)
            time.sleep(3)
            
            # Fade out
            self.fade_image(badge_img, fade_in=False, steps=10, delay=0)
            
            logging.info("Unknown face rejected with humor!")
        else:
            # Known face - show normal badge AND upload to Google Sheets
            # Get avatar path
            avatar_path = self.avatar_paths.get(username)
            
            # Upload to Google Sheets in BACKGROUND THREAD (non-blocking!)
            if ENABLE_GOOGLE_SHEETS and self.latest_frame is not None:
                self.upload_to_google_sheets(username, self.latest_frame)
            
            # Badge display continues immediately without waiting for upload!
            # Create badge screen (with appropriate message)
            badge_img = self.create_badge_screen(username, avatar_path, message=badge_message)
            
            # Fade in badge (no delay)
            self.fade_image(badge_img, fade_in=True, steps=10, delay=0)
            
            # Display for 2 seconds (reduced from 3)
            time.sleep(2)
            
            # Fade out badge (no delay)
            self.fade_image(badge_img, fade_in=False, steps=10, delay=0)
            
            logging.info("Badge display complete, returning to idle")
    
    def show_idle_screen(self):
        """Display first idle frame (used as fallback)"""
        if self.idle_frames:
            self.disp.ShowImage(self.idle_frames[0].rotate(180))
        else:
            # Fallback to black screen if no animation
            idle_img = Image.new("RGB", (LCD_SIZE, LCD_SIZE), (0, 0, 0))
            self.disp.ShowImage(idle_img.rotate(180))
        self.current_state = "idle"
    
    def cleanup(self):
        """Clean up resources"""
        logging.info("Cleaning up resources...")
        self.running = False
        
        if self.cap:
            self.cap.release()
            logging.info("Camera released")
        
        try:
            self.disp.module_exit()
            logging.info("Display cleaned up")
        except:
            pass
    
    def run(self):
        """Start the application - simple, no threading!"""
        try:
            # Just run the detection loop
            self.detect_and_show_badge()
                
        except KeyboardInterrupt:
            logging.info("Stopped by user")
        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        app = FaceBadgeSystem()
        app.run()
    except Exception as e:
        logging.error(f"Failed to start application: {e}")
        import sys
        sys.exit(1)
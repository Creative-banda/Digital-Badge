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

# Add multiple possible paths for LCD library
# Option 1: lib folder in same directory as this script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Option 2: lib folder one level up (original structure)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from lib import LCD_1inch28

logging.basicConfig(level=logging.INFO)

LCD_SIZE = 240


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
        self.load_known_faces()
        
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
        self.frames_required = 3
        self.last_detected_name = None
    
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
    
    def fade_image(self, img, fade_in=True, steps=20, delay=0.02):
        """Fade in/out an image on the LCD display"""
        black = Image.new("RGB", (LCD_SIZE, LCD_SIZE), (0, 0, 0))
        
        for i in range(steps + 1):
            alpha = i / steps if fade_in else 1 - (i / steps)
            frame = Image.blend(black, img, alpha)
            self.disp.ShowImage(frame.rotate(180))
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
    
    def create_badge_screen(self, username, avatar_path=None):
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
        
        # Draw "Welcome" text
        try:
            welcome_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                16
            )
        except:
            welcome_font = ImageFont.load_default()
        
        welcome_text = "Welcome!"
        bbox = draw.textbbox((0, 0), welcome_text, font=welcome_font)
        tw = bbox[2] - bbox[0]
        draw.text(((LCD_SIZE - tw) // 2, 210), welcome_text, fill=(100, 255, 100), font=welcome_font)
        
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
        idle_delay = 0.03  # Fast animation playback
        scan_delay = 0.02  # Even faster for scan
        detect_every_n_frames = 3  # Only detect faces every 3rd frame for speed
        frame_counter = 0
        
        while self.running:
            # Reset detection state
            self.detection_frames = 0
            self.last_detected_name = None
            self.current_state = "idle"
            
            # IDLE STATE: Play idle animation while waiting for face
            while self.running:
                # Show next idle frame if available
                if self.idle_frames:
                    self.disp.ShowImage(self.idle_frames[idle_frame_idx].rotate(180))
                    idle_frame_idx = (idle_frame_idx + 1) % len(self.idle_frames)
                
                frame_counter += 1
                
                # Only check for face every N frames to keep animation smooth
                if frame_counter % detect_every_n_frames == 0:
                    ret, frame = self.cap.read()
                    if ret:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        face_locations = face_recognition.face_locations(rgb_frame)
                        
                        if face_locations and len(self.known_face_encodings) > 0:
                            # Face detected! Switch to SCAN state
                            self.current_state = "scan"
                            scan_frame_idx = 0
                            frame_counter = 0
                            break
                
                time.sleep(idle_delay)
            
            # SCAN STATE: Play scan animation while recognizing
            recognized_user = None
            
            while self.running and self.current_state == "scan":
                # Show next scan frame if available
                if self.scan_frames:
                    self.disp.ShowImage(self.scan_frames[scan_frame_idx].rotate(180))
                    scan_frame_idx = (scan_frame_idx + 1) % len(self.scan_frames)
                
                frame_counter += 1
                
                # Check face recognition every N frames
                if frame_counter % detect_every_n_frames == 0:
                    ret, frame = self.cap.read()
                    if not ret:
                        time.sleep(scan_delay)
                        continue
                    
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_frame)
                    
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
                                tolerance=0.6
                            )
                            
                            if True in matches:
                                match_index = matches.index(True)
                                detected_name = self.known_face_names[match_index]
                                face_detected = True
                                break
                        
                        if face_detected:
                            if detected_name == self.last_detected_name:
                                self.detection_frames += 1
                            else:
                                self.detection_frames = 1
                                self.last_detected_name = detected_name
                            
                            # Stable recognition achieved!
                            if self.detection_frames >= self.frames_required and recognized_user is None:
                                logging.info(f"Face recognized: {detected_name}")
                                recognized_user = detected_name
                                # Continue playing animation, don't break yet
                        else:
                            # Face present but not recognized
                            if recognized_user is None:
                                self.detection_frames = 0
                                self.last_detected_name = None
                
                # Check if scan animation completed one full loop after recognition
                if recognized_user is not None and scan_frame_idx == 0 and frame_counter > detect_every_n_frames:
                    # Scan animation loop complete, show badge
                    self.show_badge(recognized_user)
                    frame_counter = 0
                    break
                
                time.sleep(scan_delay)
        
        logging.info("Detection stopped")
    
    def show_badge(self, username):
        """Display user badge with animation"""
        self.current_state = "badge"
        
        logging.info(f"Showing badge for: {username}")
        
        # Get avatar path
        avatar_path = self.avatar_paths.get(username)
        
        # Create badge screen
        badge_img = self.create_badge_screen(username, avatar_path)
        
        # Fade in badge
        self.fade_image(badge_img, fade_in=True)
        
        # Display for 3 seconds
        time.sleep(3)
        
        # Fade out badge
        self.fade_image(badge_img, fade_in=False)
        
        # Small pause before returning to idle animation
        time.sleep(0.5)
        
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
#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sys
import cv2
import face_recognition
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance, ImageFont
import numpy as np
import os
import time
import threading
import glob
import logging

sys.path.append("..")
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
        
        # Store multiple known faces and their data
        self.known_face_encodings = []
        self.known_face_names = []
        self.avatar_paths = {}
        self.load_known_faces()
        
        # Camera setup
        self.cap = None
        self.camera_active = False
        
        # UI state
        self.current_state = "idle"
        self.recognized_user = None
        self.running = True
        
        # Load idle screen
        self.show_idle_screen()
    
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
    
    def camera_loop(self):
        """Main camera processing loop"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logging.error("Cannot open camera")
            return
        
        self.camera_active = True
        logging.info("Camera started, waiting for faces...")
        
        while self.camera_active and self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            if self.current_state == "idle":
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Find faces in frame
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if face_locations and len(self.known_face_encodings) > 0:
                    # Encode faces
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    
                    for face_encoding in face_encodings:
                        # Compare with all known faces
                        matches = face_recognition.compare_faces(
                            self.known_face_encodings, 
                            face_encoding, 
                            tolerance=0.6
                        )
                        
                        # Check if any match found
                        if True in matches:
                            # Get the index of first match
                            match_index = matches.index(True)
                            recognized_name = self.known_face_names[match_index]
                            
                            # Face recognized - stop camera and show badge
                            self.recognized_user = recognized_name
                            self.camera_active = False
                            self.show_badge()
                            break
            
            time.sleep(0.1)  # Small delay to prevent excessive CPU usage
        
        if self.cap:
            self.cap.release()
    
    def show_badge(self):
        """Display user badge with animation"""
        self.current_state = "badge"
        
        if not self.recognized_user:
            logging.error("No recognized user")
            self.reset_to_idle()
            return
        
        username = self.recognized_user
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
        
        # Reset to idle
        time.sleep(0.5)
        self.reset_to_idle()
    
    def reset_to_idle(self):
        """Reset system to idle state"""
        self.show_idle_screen()
        self.recognized_user = None
        # Restart camera in a new thread
        camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        camera_thread.start()
    
    def run(self):
        """Start the application"""
        try:
            # Start camera thread
            camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
            camera_thread.start()
            
            # Keep main thread alive
            while self.running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logging.info("Stopped by user")
            self.running = False
            self.camera_active = False
            self.disp.module_exit()
        except Exception as e:
            logging.error(f"Error: {e}")
            self.running = False
            self.camera_active = False
            self.disp.module_exit()

if __name__ == "__main__":
    app = FaceBadgeSystem()
    app.run()
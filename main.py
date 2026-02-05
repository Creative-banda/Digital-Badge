import cv2
import face_recognition
import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import os
import time
import threading
import glob

class FaceBadgeSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Badge System")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Canvas for display
        self.canvas = Canvas(self.root, width=self.screen_width, height=self.screen_height, bg='black', highlightthickness=0)
        self.canvas.pack()
        
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
        
        # Load idle screen
        self.load_idle_screen()
        
        # Start camera thread
        self.start_camera_thread()
        
        # Bind escape key to exit
        self.root.bind('<Escape>', lambda e: self.root.quit())
    
    def load_known_faces(self):
        """Load and encode all known faces from known_faces folder"""
        known_faces_dir = "known_faces"
        
        if not os.path.exists(known_faces_dir):
            print(f"Warning: {known_faces_dir} directory not found")
            return
        
        # Supported image extensions
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        face_files = []
        
        # Get all image files
        for ext in extensions:
            face_files.extend(glob.glob(os.path.join(known_faces_dir, ext)))
        
        if not face_files:
            print(f"No face images found in {known_faces_dir}")
            return
        
        print(f"Loading {len(face_files)} face(s) from {known_faces_dir}...")
        
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
                        print(f"✓ Loaded: {username} (with avatar)")
                    else:
                        print(f"✓ Loaded: {username} (no avatar found)")
                else:
                    print(f"✗ No face detected in {filename}")
                    
            except Exception as e:
                print(f"✗ Error loading {face_file}: {str(e)}")
        
        print(f"\nTotal faces loaded: {len(self.known_face_names)}")
        if self.known_face_names:
            print(f"Recognized users: {', '.join(self.known_face_names)}")
    
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
    
    def load_idle_screen(self):
        """Load and display idle screen"""
        idle_path = "ui/idle.png"
        if os.path.exists(idle_path):
            idle_img = Image.open(idle_path)
            idle_img = idle_img.resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
            self.idle_photo = ImageTk.PhotoImage(idle_img)
            self.show_idle_screen()
        else:
            # Create simple idle screen if image doesn't exist
            self.canvas.delete("all")
            self.canvas.create_text(self.screen_width//2, self.screen_height//2, 
                                  text="Face Recognition System\nReady", 
                                  fill="white", font=("Arial", 24), justify="center")
    
    def show_idle_screen(self):
        """Display idle screen"""
        self.canvas.delete("all")
        if hasattr(self, 'idle_photo'):
            self.canvas.create_image(self.screen_width//2, self.screen_height//2, image=self.idle_photo)
        self.current_state = "idle"
    
    def start_camera_thread(self):
        """Start camera in separate thread"""
        camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        camera_thread.start()
    
    def camera_loop(self):
        """Main camera processing loop"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Cannot open camera")
            return
        
        self.camera_active = True
        
        while self.camera_active:
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
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
                        
                        # Check if any match found
                        if True in matches:
                            # Get the index of first match
                            match_index = matches.index(True)
                            recognized_name = self.known_face_names[match_index]
                            
                            # Face recognized - stop camera and show badge
                            self.recognized_user = recognized_name
                            self.camera_active = False
                            self.root.after(0, self.show_badge)
                            break
            
            time.sleep(0.1)  # Small delay to prevent excessive CPU usage
        
        if self.cap:
            self.cap.release()
    
    def show_badge(self):
        """Display user badge"""
        self.canvas.delete("all")
        self.current_state = "badge"
        
        if not self.recognized_user:
            print("Error: No recognized user")
            self.reset_to_idle()
            return
        
        username = self.recognized_user
        print(f"Showing badge for: {username}")
        
        # Check if avatar exists for this user
        avatar_path = self.avatar_paths.get(username)
        
        if avatar_path and os.path.exists(avatar_path):
            # Load and process avatar
            avatar_img = Image.open(avatar_path)
            avatar_size = 200
            avatar_img = avatar_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
            
            # Create circular mask
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            
            # Apply mask to avatar
            avatar_img.putalpha(mask)
            
            # Convert to PhotoImage
            self.avatar_photo = ImageTk.PhotoImage(avatar_img)
            
            # Display avatar
            avatar_x = self.screen_width // 2
            avatar_y = self.screen_height // 2 - 50
            self.canvas.create_image(avatar_x, avatar_y, image=self.avatar_photo)
        else:
            # Create placeholder circle if no avatar
            avatar_x = self.screen_width // 2
            avatar_y = self.screen_height // 2 - 50
            self.canvas.create_oval(avatar_x - 100, avatar_y - 100, avatar_x + 100, avatar_y + 100, 
                                  fill="gray", outline="white", width=3)
            # Add initial letter
            initial = username[0].upper() if username else "?"
            self.canvas.create_text(avatar_x, avatar_y, 
                                  text=initial, 
                                  fill="white", font=("Arial", 60, "bold"))
        
        # Display user name (capitalize first letter of each word)
        display_name = username.replace('_', ' ').title()
        name_y = self.screen_height // 2 + 120
        self.canvas.create_text(self.screen_width // 2, name_y, 
                              text=display_name, 
                              fill="white", font=("Arial", 32, "bold"))
        
        # Display welcome message
        welcome_y = name_y + 60
        self.canvas.create_text(self.screen_width // 2, welcome_y, 
                              text="Welcome!", 
                              fill="lightgreen", font=("Arial", 24))
        
        # Schedule return to idle after 5 seconds
        self.root.after(5000, self.reset_to_idle)
    
    def reset_to_idle(self):
        """Reset system to idle state"""
        self.show_idle_screen()
        # Restart camera
        self.start_camera_thread()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = FaceBadgeSystem()
    app.run()
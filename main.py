import cv2
import face_recognition
import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import os
import time
import threading

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
        
        # Load known face encoding
        self.known_face_encoding = None
        self.user_name = "John Doe"  # Default user name
        self.load_known_face()
        
        # Camera setup
        self.cap = None
        self.camera_active = False
        
        # UI state
        self.current_state = "idle"
        
        # Load idle screen
        self.load_idle_screen()
        
        # Start camera thread
        self.start_camera_thread()
        
        # Bind escape key to exit
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
    def load_known_face(self):
        """Load and encode the known face from known_faces/user.jpg"""
        known_face_path = "known_faces/user.jpg"
        if os.path.exists(known_face_path):
            known_image = face_recognition.load_image_file(known_face_path)
            encodings = face_recognition.face_encodings(known_image)
            if encodings:
                self.known_face_encoding = encodings[0]
                print("Known face loaded successfully")
            else:
                print("No face found in reference image")
        else:
            print("Reference image not found")
    
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
                
                if face_locations:
                    # Encode faces
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    
                    for face_encoding in face_encodings:
                        if self.known_face_encoding is not None:
                            # Compare with known face
                            matches = face_recognition.compare_faces([self.known_face_encoding], face_encoding, tolerance=0.6)
                            
                            if matches[0]:
                                # Face recognized - stop camera and show badge
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
        
        # Load avatar image
        avatar_path = "avatars/user_avatar.png"
        if os.path.exists(avatar_path):
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
        
        # Display user name
        name_y = self.screen_height // 2 + 120
        self.canvas.create_text(self.screen_width // 2, name_y, 
                              text=self.user_name, 
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
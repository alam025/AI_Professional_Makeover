"""
Camera Handler - OpenCV-only face detection (No MediaPipe dependency)
"""

import cv2
import numpy as np
import time

class CameraHandler:
    def __init__(self, camera_id=0):
        """Initialize camera and face detection"""
        self.camera_id = camera_id
        self.cap = None
        self.face_detected = False
        self.face_stable_time = 0
        self.last_face_time = 0
        self.face_coords = None  # Added to store face coordinates
        
        # Initialize OpenCV face detection (Haar Cascades)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Initialize camera
        self.initialize_camera()
    
    def initialize_camera(self):
        """Initialize and configure camera"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                print(f"❌ Error: Cannot open camera {self.camera_id}")
                return False
            
            # Set camera properties for best quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.6)
            self.cap.set(cv2.CAP_PROP_CONTRAST, 0.6)
            
            print("📹 Camera initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Camera initialization error: {e}")
            return False
    
    def get_frame(self):
        """Get current camera frame"""
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Enhance frame quality
        frame = self.enhance_frame(frame)
        
        return frame
    
    def enhance_frame(self, frame):
        """Enhance frame quality for better appearance"""
        # Apply slight gaussian blur for smoothing
        frame = cv2.GaussianBlur(frame, (3, 3), 0)
        
        # Enhance brightness and contrast
        alpha = 1.2  # Contrast control
        beta = 10    # Brightness control
        frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        
        # Apply color correction for better skin tones
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel for better lighting
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels and convert back
        lab = cv2.merge((l, a, b))
        frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return frame
    
    def detect_face(self, frame):
        """Detect face in frame using OpenCV Haar Cascades"""
        if frame is None:
            return False
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) > 0:
            # Get the largest face
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = largest_face
            
            # Store face coordinates for drawing
            self.face_coords = (x, y, w, h)
            
            # Check face size (ensure it's large enough)
            face_area = w * h
            frame_area = frame.shape[0] * frame.shape[1]
            face_ratio = face_area / frame_area
            
            if face_ratio > 0.02:  # Face should be at least 2% of frame
                self.face_detected = True
                self.last_face_time = time.time()
                return True
        
        # Check if face was lost recently
        if time.time() - self.last_face_time > 1.0:  # 1 second tolerance
            self.face_detected = False
            self.face_coords = None
        
        return self.face_detected

    def draw_face_detection(self, frame):
        """Draw face detection indicator - THIS WAS THE MISSING METHOD"""
        if self.face_detected and self.face_coords is not None:
            x, y, w, h = self.face_coords
            
            # Draw green rectangle around face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Add "Face Detected" text
            cv2.putText(frame, "Face Detected!", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame
    
    def get_person_mask(self, frame):
        """Get person segmentation mask (simplified version)"""
        if frame is None:
            return None
        
        # Simple background subtraction approach
        height, width = frame.shape[:2]
        
        # Create a simple oval mask for person (center of frame)
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Create an oval mask in the center (person area approximation)
        center_x, center_y = width // 2, height // 2
        cv2.ellipse(mask, (center_x, center_y), 
                   (width // 3, height // 2), 0, 0, 360, 255, -1)
        
        # Apply gaussian blur for soft edges
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        
        return mask
    
    def get_upper_body_mask(self, frame):
        """Get upper body region mask for clothing application"""
        person_mask = self.get_person_mask(frame)
        if person_mask is None:
            return None
        
        # Focus on upper 60% of the person
        h, w = person_mask.shape
        upper_body_mask = person_mask.copy()
        
        # Mask out lower 40% of the person
        upper_body_mask[int(h * 0.6):, :] = 0
        
        return upper_body_mask
    
    def release(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()
        print("📹 Camera released successfully!")
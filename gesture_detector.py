"""
Gesture Detector - Hand tracking and finger click detection
Uses MediaPipe Hands for precise finger tracking
"""

import cv2
import numpy as np
import mediapipe as mp
import time

class GestureDetector:
    def __init__(self):
        """Initialize gesture detection with MediaPipe Hands"""
        # MediaPipe Hands initialization
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Gesture state
        self.finger_pos = None
        self.last_pos = None
        self.is_clicking = False
        self.hold_start_time = None
        self.hold_threshold = 1.5  # 1.5 seconds to trigger click
        self.position_threshold = 30  # pixels
        
        # Calibration
        self.calibrated = False
        self.calibration_frames = 0
        
        print("Gesture detector initialized with MediaPipe Hands")
    
    def detect_finger_click(self, frame):
        """
        Detect index finger position and click gesture (hold)
        Returns: (finger_position, is_clicking)
        """
        if frame is None:
            return None, False
        
        try:
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            results = self.hands.process(rgb_frame)
            
            # Auto-calibrate
            if not self.calibrated:
                self.calibration_frames += 1
                if self.calibration_frames > 30:
                    self.calibrated = True
                    print("Gesture detector calibrated!")
            
            if results.multi_hand_landmarks:
                # Get first hand
                hand_landmarks = results.multi_hand_landmarks[0]
                
                # Get index finger tip (landmark 8)
                h, w = frame.shape[:2]
                index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                
                finger_x = int(index_tip.x * w)
                finger_y = int(index_tip.y * h)
                
                self.finger_pos = (finger_x, finger_y)
                
                # Check for hold gesture (finger staying in same position)
                if self.last_pos is not None:
                    distance = np.sqrt((finger_x - self.last_pos[0])**2 + 
                                     (finger_y - self.last_pos[1])**2)
                    
                    if distance < self.position_threshold:
                        # Finger is holding position
                        if self.hold_start_time is None:
                            self.hold_start_time = time.time()
                        else:
                            hold_duration = time.time() - self.hold_start_time
                            
                            if hold_duration >= self.hold_threshold:
                                # Trigger click
                                self.is_clicking = True
                                self.hold_start_time = None  # Reset
                                return self.finger_pos, True
                    else:
                        # Finger moved, reset hold timer
                        self.hold_start_time = None
                        self.is_clicking = False
                else:
                    self.hold_start_time = None
                
                self.last_pos = self.finger_pos
                return self.finger_pos, False
            
            else:
                # No hand detected
                self.finger_pos = None
                self.last_pos = None
                self.hold_start_time = None
                self.is_clicking = False
                return None, False
                
        except Exception as e:
            print(f"Gesture detection error: {e}")
            return None, False
    
    def get_click_progress(self):
        """Get progress of hold gesture (0.0 to 1.0)"""
        if self.hold_start_time is None:
            return 0.0
        
        hold_duration = time.time() - self.hold_start_time
        progress = min(hold_duration / self.hold_threshold, 1.0)
        return progress
    
    def reset(self):
        """Reset gesture state"""
        self.finger_pos = None
        self.last_pos = None
        self.hold_start_time = None
        self.is_clicking = False
    
    def is_calibrated(self):
        """Check if detector is calibrated"""
        return self.calibrated
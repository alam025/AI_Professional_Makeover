"""
Background Engine - Fixed Version
- Prevents face cutoff
- Better person segmentation using MediaPipe
- Improved edge blending
"""

import cv2
import numpy as np
import os
import mediapipe as mp

class BackgroundEngine:
    def __init__(self):
        """Initialize background replacement with MediaPipe"""
        self.current_background = None
        
        # Initialize MediaPipe Selfie Segmentation
        self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
        self.selfie_segmentation = self.mp_selfie_segmentation.SelfieSegmentation(
            model_selection=1  # 1 for general model (better for full body)
        )
        
        print("MediaPipe Background engine initialized!")

    def change_background(self, background_path):
        """Change background instantly"""
        try:
            if os.path.exists(background_path):
                self.current_background = cv2.imread(background_path)
                print(f"Background loaded: {os.path.basename(background_path)}")
                return True
            else:
                print(f"Background not found: {background_path}")
                return False
        except Exception as e:
            print(f"Background load error: {e}")
            return False

    def apply_background(self, frame, background_path=None):
        """
        Apply background with improved person segmentation
        - Prevents face cutoff
        - Better edge detection
        - Smooth blending
        """
        if background_path and background_path != getattr(self, 'last_bg_path', None):
            self.change_background(background_path)
            self.last_bg_path = background_path
        
        if self.current_background is None:
            return frame
        
        try:
            # Get high-quality person mask
            person_mask = self.get_improved_person_mask(frame)
            
            if person_mask is None:
                return frame
            
            # Resize background to match frame
            h, w = frame.shape[:2]
            background = cv2.resize(self.current_background, (w, h))
            
            # Apply improved background replacement
            result = self.apply_smooth_background_replacement(frame, background, person_mask)
            
            return result
            
        except Exception as e:
            print(f"Background application error: {e}")
            return frame

    def get_improved_person_mask(self, frame):
        """
        Get improved person mask using MediaPipe
        - Better edge detection
        - Prevents face cutoff
        - Smoother transitions
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame with MediaPipe
        results = self.selfie_segmentation.process(rgb_frame)
        
        if results.segmentation_mask is not None:
            # Get segmentation mask
            segmentation_mask = results.segmentation_mask
            
            # Convert to binary mask with higher threshold to prevent cutoff
            # Use 0.3 threshold instead of 0.5 to include more of the person
            binary_mask = (segmentation_mask > 0.3).astype(np.uint8) * 255
            
            # Apply morphological operations to improve mask quality
            # Close small holes
            kernel = np.ones((5, 5), np.uint8)
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
            
            # Dilate slightly to ensure full person is included (prevents cutoff)
            kernel_dilate = np.ones((7, 7), np.uint8)
            binary_mask = cv2.dilate(binary_mask, kernel_dilate, iterations=1)
            
            # Apply strong smoothing for natural edges
            binary_mask = cv2.GaussianBlur(binary_mask, (11, 11), 0)
            
            return binary_mask
        
        return None

    def apply_smooth_background_replacement(self, frame, background, person_mask):
        """
        Apply smooth background replacement
        - Prevents face cutoff
        - Natural edge blending
        - High quality result
        """
        # Normalize mask to 0-1 range
        mask_normalized = person_mask.astype(np.float32) / 255.0
        
        # Create 3-channel mask
        mask_3d = np.stack([mask_normalized] * 3, axis=2)
        
        # Apply background replacement with smooth blending
        # Person areas = original frame (with higher weight to prevent cutoff)
        # Background areas = new background
        person_part = frame.astype(np.float32) * mask_3d
        background_part = background.astype(np.float32) * (1.0 - mask_3d)
        
        result = person_part + background_part
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        # Apply slight blur at the boundaries for even smoother transition
        edge_mask = cv2.Canny(person_mask, 50, 150)
        edge_mask = cv2.dilate(edge_mask, np.ones((5, 5), np.uint8), iterations=1)
        edge_mask = cv2.GaussianBlur(edge_mask, (9, 9), 0)
        
        # Blend edges
        edge_normalized = edge_mask.astype(np.float32) / 255.0
        edge_3d = np.stack([edge_normalized] * 3, axis=2)
        
        # Apply slight blur only at edges
        blurred_result = cv2.GaussianBlur(result, (5, 5), 0)
        final_result = (result.astype(np.float32) * (1.0 - edge_3d) + 
                       blurred_result.astype(np.float32) * edge_3d)
        
        return final_result.astype(np.uint8)

    def reset_background_learning(self):
        """Reset (not needed for MediaPipe)"""
        print("Background engine ready")
    
    def get_learning_progress(self):
        """Always ready with MediaPipe"""
        return 100
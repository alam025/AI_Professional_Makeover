"""
HYBRID CLOTHING ENGINE - DUAL METHOD
- T-shirts: HSV color replacement (trapezoidal mask)
- Shirts: Actual clothing overlay (proper image overlay)
"""

import cv2
import numpy as np
import os

class ProfessionalClothingEngine:
    def __init__(self, replicate_api_key=None):
        """Initialize hybrid clothing engine"""
        self.clothing_templates = {}
        self.current_outfit = None
        self.current_outfit_type = None
        
        # For T-shirt HSV method
        self.tshirt_mask = None
        
        # For Shirt overlay method
        self.cached_position = None
        self.position_stable_frames = 0
        self.min_stable_frames = 5
        
        # Load clothing
        self.load_clothing_images()
    
    def load_clothing_images(self):
        """Load clothing images"""
        clothing_types = ['tshirts', 'shirts', 'blazers', 'ties']
        
        for clothing_type in clothing_types:
            folder_path = f"assets/clothing/{clothing_type}"
            os.makedirs(folder_path, exist_ok=True)
            self.clothing_templates[clothing_type] = []
            
            if os.path.exists(folder_path):
                files = sorted([f for f in os.listdir(folder_path) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
                
                for filename in files:
                    file_path = os.path.join(folder_path, filename)
                    img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        self.clothing_templates[clothing_type].append({
                            'image': img,
                            'name': filename,
                            'color_hue': None  # Only used for t-shirts
                        })
    
    def train_background(self, frame):
        """Dummy function - not needed"""
        return True
    
    # ============= T-SHIRT METHOD (HSV Color Replacement) =============
    
    def create_simple_upper_body_mask(self, frame):
        """
        Create PROPER TRAPEZOIDAL mask for T-SHIRT color replacement
        - NARROWER at top (shoulders)
        - WIDER at bottom (waist)
        - Reduced bottom width
        """
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # T-shirt area - PROPER TRAPEZOID (narrow top, wider bottom)
        top_y = int(h * 0.65)
        bottom_y = int(h * 1.00)
        
        # NARROW at top (shoulders) - creates trapezoid shape
        top_left_x = int(w * 0.35)    # Narrower at top
        top_right_x = int(w * 0.65)   # Narrower at top
        
        # WIDER at bottom but REDUCED by 1cm (about 5% less width)
        bottom_left_x = int(w * 0.25)   # Wider at bottom (but reduced from 0.20)
        bottom_right_x = int(w * 0.75)  # Wider at bottom (but reduced from 0.80)
        
        # Create TRAPEZOID points (narrow->wide from top to bottom)
        trapezoid_points = np.array([
            [top_left_x, top_y],        # Top-left (narrow)
            [top_right_x, top_y],       # Top-right (narrow)
            [bottom_right_x, bottom_y], # Bottom-right (wide)
            [bottom_left_x, bottom_y]   # Bottom-left (wide)
        ], dtype=np.int32)
        
        cv2.fillPoly(mask, [trapezoid_points], 255)
        
        # Exclude face
        face_center_x = w // 2
        face_center_y = int(h * 0.20)
        face_radius = int(h * 0.15)
        face_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(face_mask, (face_center_x, face_center_y), face_radius, 255, -1)
        mask = cv2.subtract(mask, face_mask)
        
        # Minimal arm exclusion (only far edges)
        arm_exclusion_left = np.zeros((h, w), dtype=np.uint8)
        arm_exclusion_right = np.zeros((h, w), dtype=np.uint8)
        cv2.rectangle(arm_exclusion_left, (0, 0), (int(w * 0.18), h), 255, -1)
        cv2.rectangle(arm_exclusion_right, (int(w * 0.82), 0), (w, h), 255, -1)
        mask = cv2.subtract(mask, arm_exclusion_left)
        mask = cv2.subtract(mask, arm_exclusion_right)
        
        # Smooth edges
        mask = cv2.GaussianBlur(mask, (31, 31), 0)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        
        return mask
    
    def extract_dominant_color(self, clothing_img):
        """Extract dominant hue from clothing image (for t-shirts)"""
        try:
            if clothing_img.shape[2] == 4:
                bgr = clothing_img[:, :, :3]
                alpha = clothing_img[:, :, 3]
                mask = alpha > 50
                pixels = bgr[mask] if np.any(mask) else bgr.reshape(-1, 3)
            else:
                h, w = clothing_img.shape[:2]
                center_region = clothing_img[h//4:3*h//4, w//4:3*w//4]
                pixels = center_region.reshape(-1, 3)
            
            if len(pixels) == 0:
                return 100
            
            pixels_hsv = cv2.cvtColor(pixels.reshape(1, -1, 3), cv2.COLOR_BGR2HSV)
            mean_hue = int(np.mean(pixels_hsv[0, :, 0]))
            return mean_hue
        except:
            return 100
    
    def replace_color_simple(self, frame, mask, target_hue):
        """HSV color replacement (for t-shirts)"""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            
            h_modified = h.copy()
            h_modified[mask > 128] = target_hue
            
            s_modified = s.copy()
            s_modified[mask > 128] = np.clip(s[mask > 128] * 1.3, 0, 255).astype(np.uint8)
            
            hsv_modified = cv2.merge([h_modified, s_modified, v])
            result = cv2.cvtColor(hsv_modified, cv2.COLOR_HSV2BGR)
            return result
        except:
            return frame
    
    def apply_tshirt_color_replacement(self, frame, clothing_item):
        """Apply HSV color replacement for T-SHIRTS"""
        try:
            clothing_img = clothing_item['image']
            
            # Extract target color if not cached
            if clothing_item['color_hue'] is None:
                clothing_item['color_hue'] = self.extract_dominant_color(clothing_img)
            
            target_hue = clothing_item['color_hue']
            
            # Create mask
            mask = self.create_simple_upper_body_mask(frame)
            self.tshirt_mask = mask
            
            # Replace color
            result = self.replace_color_simple(frame, mask, target_hue)
            return result
        except Exception as e:
            print(f"T-shirt color replacement error: {e}")
            return frame
    
    # ============= SHIRT METHOD (Actual Clothing Overlay) =============
    
    def detect_upper_body_region(self, frame):
        """
        Detect upper body region for SHIRT overlay placement
        FIXED: Starts BELOW face (not covering face)
        """
        h, w = frame.shape[:2]
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        if len(faces) > 0:
            fx, fy, fw, fh = max(faces, key=lambda x: x[2] * x[3])
            
            # CRITICAL: Start WELL BELOW face (at neck/collar area)
            # Increased gap to ensure face is never covered
            collar_y = fy + fh + int(fh * 0.5)  # Changed from 0.3 to 0.5 (more gap below chin)
            
            # Width - reasonable for shirt
            torso_width = int(fw * 3.0)  # Reduced from 3.5 to 3.0 (narrower shirt)
            torso_x = fx + fw // 2 - torso_width // 2
            
            # Length - extend to bottom but not too long
            clothing_height = h - collar_y
            min_height = int(fh * 4.0)  # Reduced from 5.0 to 4.0
            if clothing_height < min_height:
                clothing_height = min_height
            
            # Ensure clothing doesn't go too high (protect face)
            if collar_y < fy + fh:
                collar_y = fy + fh + 20  # Force minimum 20px gap below face
            
            # Bounds check
            torso_x = max(0, min(torso_x, w - torso_width))
            collar_y = max(fy + fh + 20, min(collar_y, h - clothing_height))  # Never above face
            torso_width = min(torso_width, w - torso_x)
            clothing_height = min(clothing_height, h - collar_y)
            
            return (torso_x, collar_y, torso_width, clothing_height)
        
        # Fallback - ensure starts below top
        center_x = w // 2
        default_width = int(w * 0.45)  # Reduced from 0.5
        default_height = int(h * 0.6)  # Reduced from 0.7
        default_x = center_x - default_width // 2
        default_y = int(h * 0.35)  # Start lower (was 0.3)
        
        return (default_x, default_y, default_width, default_height)
    
    def create_tshirt_mask_with_sleeves(self, width, height, corner_radius):
        """Create shirt mask with sleeves"""
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Main body
        cv2.rectangle(mask, (0, corner_radius), (width, height), 255, -1)
        cv2.rectangle(mask, (corner_radius, 0), (width - corner_radius, height), 255, -1)
        
        # Rounded corners
        cv2.circle(mask, (corner_radius, corner_radius), corner_radius, 255, -1)
        cv2.circle(mask, (width - corner_radius, corner_radius), corner_radius, 255, -1)
        
        # Sleeves
        sleeve_length = int(height * 0.70)
        sleeve_width = int(width * 0.30)
        
        cv2.rectangle(mask, (0, 0), (sleeve_width, sleeve_length), 255, -1)
        cv2.rectangle(mask, (width - sleeve_width, 0), (width, sleeve_length), 255, -1)
        
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        return mask, 0
    
    def prepare_clothing_overlay(self, clothing_img, target_width, target_height):
        """
        Prepare clothing for overlay with AGGRESSIVE BACKGROUND REMOVAL
        """
        corner_radius = int(target_width * 0.08)
        tshirt_mask, sleeve_extension = self.create_tshirt_mask_with_sleeves(
            target_width, target_height, corner_radius
        )
        
        # Resize clothing
        resized_clothing = cv2.resize(clothing_img, (target_width, target_height))
        
        # CRITICAL: Aggressive background removal for all images
        if resized_clothing.shape[2] == 4:
            # Has alpha channel - use it BUT also check for white
            bgr = resized_clothing[:, :, :3]
            alpha_original = resized_clothing[:, :, 3]
            
            # Also remove white background even if alpha exists
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            lower_white = np.array([0, 0, 220])
            upper_white = np.array([180, 25, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            alpha_from_white = cv2.bitwise_not(white_mask)
            
            # Combine both alphas (intersection)
            alpha = cv2.bitwise_and(alpha_original, alpha_from_white)
        else:
            # No alpha channel - AGGRESSIVE WHITE BACKGROUND REMOVAL
            bgr = resized_clothing
            
            # Method 1: HSV-based white detection (more aggressive)
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            lower_white = np.array([0, 0, 220])    # Very sensitive to white
            upper_white = np.array([180, 25, 255]) # Catch all whites
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            
            # Method 2: RGB-based bright pixel detection
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            _, bright_mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
            
            # Combine both methods (union - remove more background)
            combined_bg_mask = cv2.bitwise_or(white_mask, bright_mask)
            
            # Invert - we want shirt, not background
            alpha = cv2.bitwise_not(combined_bg_mask)
            
            # Clean up with morphological operations
            kernel_small = np.ones((3, 3), np.uint8)
            kernel_large = np.ones((7, 7), np.uint8)
            
            # Remove small noise
            alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel_small)
            # Fill small holes in shirt
            alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel_large)
            # Erode slightly to remove edge artifacts
            alpha = cv2.erode(alpha, kernel_small, iterations=2)
            # Smooth edges
            alpha = cv2.GaussianBlur(alpha, (7, 7), 0)
        
        # Final cleanup - ensure no stray pixels
        _, alpha = cv2.threshold(alpha, 50, 255, cv2.THRESH_BINARY)
        
        # Combine with T-shirt mask
        combined_alpha = cv2.bitwise_and(alpha, tshirt_mask)
        
        return bgr, combined_alpha, sleeve_extension
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """Apply actual clothing overlay for SHIRTS"""
        try:
            clothing_img = clothing_item['image']
            
            # Detect upper body
            cloth_x, cloth_y, cloth_w, cloth_h = self.detect_upper_body_region(frame)
            
            # Prepare overlay
            clothing_bgr, clothing_alpha, sleeve_extension = self.prepare_clothing_overlay(
                clothing_img, cloth_w, cloth_h
            )
            
            extended_x = cloth_x - sleeve_extension
            extended_w = cloth_w + 2 * sleeve_extension
            
            result = frame.copy()
            h, w = result.shape[:2]
            
            # Crop if out of bounds
            if extended_x < 0:
                crop_left = -extended_x
                extended_x = 0
                clothing_bgr = clothing_bgr[:, crop_left:]
                clothing_alpha = clothing_alpha[:, crop_left:]
                extended_w = clothing_bgr.shape[1]
            
            if extended_x + extended_w > w:
                crop_right = w - extended_x
                clothing_bgr = clothing_bgr[:, :crop_right]
                clothing_alpha = clothing_alpha[:, :crop_right]
                extended_w = clothing_bgr.shape[1]
            
            if cloth_y + cloth_h > h:
                crop_bottom = h - cloth_y
                clothing_bgr = clothing_bgr[:crop_bottom, :]
                clothing_alpha = clothing_alpha[:crop_bottom, :]
                cloth_h = clothing_bgr.shape[0]
            
            # Get ROI
            roi = result[cloth_y:cloth_y + cloth_h, extended_x:extended_x + extended_w]
            
            # Resize if needed
            if roi.shape[0] != clothing_bgr.shape[0] or roi.shape[1] != clothing_bgr.shape[1]:
                clothing_bgr = cv2.resize(clothing_bgr, (roi.shape[1], roi.shape[0]))
                clothing_alpha = cv2.resize(clothing_alpha, (roi.shape[1], roi.shape[0]))
            
            # Alpha blend
            alpha_normalized = clothing_alpha.astype(float) / 255.0
            alpha_3d = np.stack([alpha_normalized] * 3, axis=2)
            
            blended = (clothing_bgr.astype(float) * alpha_3d + 
                      roi.astype(float) * (1.0 - alpha_3d))
            
            result[cloth_y:cloth_y + cloth_h, extended_x:extended_x + extended_w] = blended.astype(np.uint8)
            
            return result
        except Exception as e:
            print(f"Shirt overlay error: {e}")
            return frame
    
    # ============= MAIN APPLICATION METHOD =============
    
    def apply_clothing_item(self, frame, clothing_type, item_index):
        """
        Main method - Routes to appropriate technique:
        - T-shirts → HSV color replacement
        - Shirts → Actual clothing overlay
        """
        if frame is None:
            return frame
        
        try:
            items = self.clothing_templates.get(clothing_type, [])
            if item_index >= len(items):
                return frame
            
            clothing_item = items[item_index]
            
            # ROUTE BASED ON CLOTHING TYPE
            if clothing_type == "tshirts":
                # HSV Color Replacement Method
                result = self.apply_tshirt_color_replacement(frame, clothing_item)
                print(f"🎨 Applied T-shirt color replacement (HSV)")
            
            elif clothing_type == "shirts":
                # Actual Clothing Overlay Method
                result = self.apply_shirt_overlay(frame, clothing_item)
                print(f"👔 Applied shirt overlay (actual image)")
            
            else:
                # Default for other types
                result = frame
            
            self.current_outfit = clothing_item
            self.current_outfit_type = clothing_type
            
            return result
            
        except Exception as e:
            print(f"❌ Clothing application error: {e}")
            import traceback
            traceback.print_exc()
            return frame
    
    def debug_draw_body_landmarks(self, frame):
        """Debug visualization"""
        if self.tshirt_mask is not None:
            result = frame.copy()
            
            h, w = frame.shape[:2]
            # Updated to match PROPER TRAPEZOID dimensions
            top_y = int(h * 0.65)
            bottom_y = int(h * 1.00)
            top_left_x = int(w * 0.35)    # Narrow at top
            top_right_x = int(w * 0.65)   # Narrow at top
            bottom_left_x = int(w * 0.25) # Wide at bottom
            bottom_right_x = int(w * 0.75) # Wide at bottom
            
            trapezoid_points = np.array([
                [top_left_x, top_y],
                [top_right_x, top_y],
                [bottom_right_x, bottom_y],
                [bottom_left_x, bottom_y]
            ], dtype=np.int32)
            
            cv2.polylines(result, [trapezoid_points], True, (0, 255, 255), 2)
            
            cv2.putText(result, "TRAPEZOID MASK (Narrow->Wide)", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(result, "Top: Narrow | Bottom: Wide", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            return result
        
        return frame
    
    def reset_pose_history(self):
        """Reset"""
        self.tshirt_mask = None
        self.cached_position = None
    
    def clear_cache(self):
        """Clear cache"""
        for clothing_type in self.clothing_templates:
            for item in self.clothing_templates[clothing_type]:
                item['color_hue'] = None
    
    def set_quality_mode(self, high_quality=True):
        pass
    
    def get_performance_stats(self):
        return {
            'background_trained': True,
            'cached_colors': sum(1 for ct in self.clothing_templates.values() 
                               for item in ct if item['color_hue'] is not None)
        }
    
    def get_available_clothing(self, clothing_type):
        return self.clothing_templates.get(clothing_type, [])
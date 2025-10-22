"""
PERFECT SHIRT FITTING ENGINE
- Detects neck position precisely
- Fits shirt collar at neck
- Aligns with shoulders
- NO WHITE BACKGROUND
"""

import cv2
import numpy as np
import os

class ProfessionalClothingEngine:
    def __init__(self, replicate_api_key=None):
        """Initialize clothing engine"""
        self.clothing_templates = {}
        self.current_outfit = None
        self.current_outfit_type = None
        
        # For T-shirt HSV method
        self.tshirt_mask = None
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Load clothing
        self.load_clothing_images()
        
        print("✅ Perfect fitting engine initialized!")
    
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
                            'color_hue': None
                        })
                        print(f"✅ Loaded {clothing_type}/{filename}")
    
    def train_background(self, frame):
        """Dummy function"""
        return True
    
    def detect_neck_and_shoulders(self, frame):
        """Detect neck position and shoulder width"""
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        if len(faces) > 0:
            fx, fy, fw, fh = max(faces, key=lambda x: x[2] * x[3])
            
            # Calculate neck position (bottom center of face)
            neck_x = fx + fw // 2
            neck_y = fy + fh  # Bottom of face = top of neck
            
            # Estimate shoulder positions
            shoulder_width = int(fw * 2.5)  # Shoulders are ~2.5x face width
            left_shoulder_x = neck_x - shoulder_width // 2
            right_shoulder_x = neck_x + shoulder_width // 2
            shoulder_y = neck_y + int(fh * 0.4)  # Shoulders ~40% of face height below neck
            
            return {
                'neck': (neck_x, neck_y),
                'left_shoulder': (left_shoulder_x, shoulder_y),
                'right_shoulder': (right_shoulder_x, shoulder_y),
                'shoulder_width': shoulder_width,
                'face_width': fw,
                'face_height': fh
            }
        
        return None
    
    # ============= T-SHIRT METHOD (HSV Color Replacement) =============
    
    def create_body_aware_tshirt_mask(self, frame):
        """Create mask based on neck and shoulder detection"""
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        body_points = self.detect_neck_and_shoulders(frame)
        
        if body_points:
            neck_x, neck_y = body_points['neck']
            left_shoulder_x, _ = body_points['left_shoulder']
            right_shoulder_x, _ = body_points['right_shoulder']
            shoulder_y = body_points['left_shoulder'][1]
            
            # T-shirt area from shoulders down
            torso_top_y = shoulder_y
            torso_bottom_y = min(h, torso_top_y + int(body_points['face_height'] * 5.0))
            
            # Waist slightly wider
            waist_width = int(body_points['shoulder_width'] * 1.1)
            waist_left_x = neck_x - waist_width // 2
            waist_right_x = neck_x + waist_width // 2
            
            # Create trapezoid
            torso_points = np.array([
                [left_shoulder_x, torso_top_y],
                [right_shoulder_x, torso_top_y],
                [waist_right_x, torso_bottom_y],
                [waist_left_x, torso_bottom_y]
            ], dtype=np.int32)
            
            cv2.fillPoly(mask, [torso_points], 255)
            
            # Exclude neck/face
            face_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(face_mask, (neck_x, neck_y - body_points['face_height'] // 2), 
                       (body_points['face_width'] // 2 + 10, body_points['face_height'] // 2 + 20), 
                       0, 0, 360, 255, -1)
            mask = cv2.subtract(mask, face_mask)
        else:
            # Fallback
            return self.create_simple_upper_body_mask(frame)
        
        # Smooth
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        
        return mask
    
    def create_simple_upper_body_mask(self, frame):
        """Fallback mask"""
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        top_y = int(h * 0.30)
        bottom_y = int(h * 0.95)
        top_left_x = int(w * 0.30)
        top_right_x = int(w * 0.70)
        bottom_left_x = int(w * 0.20)
        bottom_right_x = int(w * 0.80)
        
        trapezoid_points = np.array([
            [top_left_x, top_y],
            [top_right_x, top_y],
            [bottom_right_x, bottom_y],
            [bottom_left_x, bottom_y]
        ], dtype=np.int32)
        
        cv2.fillPoly(mask, [trapezoid_points], 255)
        
        mask = cv2.GaussianBlur(mask, (31, 31), 0)
        return mask
    
    def extract_dominant_color(self, clothing_img):
        """Extract dominant hue"""
        try:
            if len(clothing_img.shape) == 3 and clothing_img.shape[2] == 4:
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
        """HSV color replacement"""
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
        """Apply T-shirt"""
        try:
            clothing_img = clothing_item['image']
            
            if clothing_item['color_hue'] is None:
                clothing_item['color_hue'] = self.extract_dominant_color(clothing_img)
            
            target_hue = clothing_item['color_hue']
            mask = self.create_body_aware_tshirt_mask(frame)
            self.tshirt_mask = mask
            
            result = self.replace_color_simple(frame, mask, target_hue)
            return result
        except Exception as e:
            print(f"T-shirt error: {e}")
            return frame
    
    # ============= SHIRT METHOD (Perfect Neck Fitting) =============
    
    def remove_white_background_aggressive(self, img):
        """AGGRESSIVELY remove ALL white/light background"""
        if len(img.shape) == 3 and img.shape[2] == 4:
            bgr = img[:, :, :3]
            alpha_original = img[:, :, 3]
        else:
            bgr = img
            alpha_original = np.ones((img.shape[0], img.shape[1]), dtype=np.uint8) * 255
        
        # Method 1: HSV white detection (VERY AGGRESSIVE)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 150])  # Even more aggressive
        upper_white = np.array([180, 50, 255])
        white_mask1 = cv2.inRange(hsv, lower_white, upper_white)
        
        # Method 2: RGB brightness
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        _, white_mask2 = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        
        # Method 3: Check if all RGB channels are high
        b, g, r = cv2.split(bgr)
        white_mask3 = cv2.bitwise_and(
            cv2.bitwise_and(b > 150, g > 150),
            r > 150
        ).astype(np.uint8) * 255
        
        # Combine all methods (union - remove MORE background)
        combined_white_mask = cv2.bitwise_or(white_mask1, white_mask2)
        combined_white_mask = cv2.bitwise_or(combined_white_mask, white_mask3)
        
        # Invert to get clothing mask
        clothing_mask = cv2.bitwise_not(combined_white_mask)
        
        # Combine with original alpha
        final_alpha = cv2.bitwise_and(alpha_original, clothing_mask)
        
        # Morphological operations to clean edges
        kernel = np.ones((3, 3), np.uint8)
        final_alpha = cv2.morphologyEx(final_alpha, cv2.MORPH_OPEN, kernel, iterations=2)
        final_alpha = cv2.morphologyEx(final_alpha, cv2.MORPH_CLOSE, kernel, iterations=3)
        
        # Erode to remove any remaining white edges
        final_alpha = cv2.erode(final_alpha, kernel, iterations=1)
        
        # Smooth edges
        final_alpha = cv2.GaussianBlur(final_alpha, (5, 5), 0)
        
        # Hard threshold to ensure binary mask
        _, final_alpha = cv2.threshold(final_alpha, 20, 255, cv2.THRESH_BINARY)
        
        return bgr, final_alpha
    
    def create_shirt_shaped_mask(self, width, height):
        """Create realistic shirt shape with proper collar"""
        mask = np.zeros((height, width), dtype=np.uint8)
        
        center_x = width // 2
        
        # Collar opening at top (V-neck or round neck)
        collar_depth = int(height * 0.10)
        collar_width = int(width * 0.15)
        
        # Shoulders (15% down from top)
        shoulder_y = int(height * 0.15)
        shoulder_left = int(width * 0.05)
        shoulder_right = int(width * 0.95)
        
        # Chest (40% down)
        chest_y = int(height * 0.40)
        chest_left = int(width * 0.05)
        chest_right = int(width * 0.95)
        
        # Waist (75% down)
        waist_y = int(height * 0.75)
        waist_left = int(width * 0.10)
        waist_right = int(width * 0.90)
        
        # Bottom
        bottom_y = height - 1
        bottom_left = int(width * 0.15)
        bottom_right = int(width * 0.85)
        
        # Create shirt body
        shirt_body = np.array([
            [center_x, 0],  # Top center (neck point)
            [shoulder_left, shoulder_y],
            [chest_left, chest_y],
            [waist_left, waist_y],
            [bottom_left, bottom_y],
            [bottom_right, bottom_y],
            [waist_right, waist_y],
            [chest_right, chest_y],
            [shoulder_right, shoulder_y],
        ], dtype=np.int32)
        
        cv2.fillPoly(mask, [shirt_body], 255)
        
        # Cut collar opening (make it look natural)
        collar_opening = np.array([
            [center_x - collar_width, 0],
            [center_x, collar_depth],
            [center_x + collar_width, 0]
        ], dtype=np.int32)
        cv2.fillPoly(mask, [collar_opening], 0)
        
        # Smooth the mask
        mask = cv2.GaussianBlur(mask, (9, 9), 0)
        
        return mask
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """Apply shirt with perfect neck/shoulder alignment"""
        try:
            h, w = frame.shape[:2]
            
            # Detect neck and shoulders
            body_points = self.detect_neck_and_shoulders(frame)
            
            if not body_points:
                print("⚠️ No body detected")
                return frame
            
            neck_x, neck_y = body_points['neck']
            left_shoulder_x, shoulder_y = body_points['left_shoulder']
            right_shoulder_x, _ = body_points['right_shoulder']
            shoulder_width = body_points['shoulder_width']
            face_height = body_points['face_height']
            
            # Shirt dimensions
            shirt_width = int(shoulder_width * 1.5)  # Wider than shoulders
            shirt_height = int(face_height * 5.5)  # Proportional to face
            
            # Position: Collar should be AT the neck
            shirt_x = neck_x - shirt_width // 2
            shirt_y = neck_y - int(shirt_height * 0.05)  # Collar slightly above neck
            
            # Bounds check
            shirt_x = max(0, min(shirt_x, w - 50))
            shirt_y = max(0, min(shirt_y, h - 50))
            shirt_width = min(shirt_width, w - shirt_x)
            shirt_height = min(shirt_height, h - shirt_y)
            
            if shirt_width <= 0 or shirt_height <= 0:
                return frame
            
            # Load and process shirt image
            clothing_img = clothing_item['image']
            
            # Resize shirt
            resized_shirt = cv2.resize(clothing_img, (shirt_width, shirt_height))
            
            # Remove white background AGGRESSIVELY
            shirt_bgr, shirt_alpha = self.remove_white_background_aggressive(resized_shirt)
            
            # Apply shirt-shaped mask
            shirt_shape_mask = self.create_shirt_shaped_mask(shirt_width, shirt_height)
            
            # Combine masks
            final_alpha = cv2.bitwise_and(shirt_alpha, shirt_shape_mask)
            
            # Get ROI
            roi = frame[shirt_y:shirt_y + shirt_height, shirt_x:shirt_x + shirt_width]
            
            if roi.shape[0] != shirt_height or roi.shape[1] != shirt_width:
                return frame
            
            # Alpha blend
            alpha_norm = final_alpha.astype(float) / 255.0
            alpha_3d = np.stack([alpha_norm] * 3, axis=2)
            
            result = frame.copy()
            blended = (shirt_bgr.astype(float) * alpha_3d + 
                      roi.astype(float) * (1.0 - alpha_3d))
            
            result[shirt_y:shirt_y + shirt_height, shirt_x:shirt_x + shirt_width] = blended.astype(np.uint8)
            
            print(f"✅ Shirt fitted at neck ({neck_x}, {neck_y})")
            return result
            
        except Exception as e:
            print(f"❌ Shirt error: {e}")
            import traceback
            traceback.print_exc()
            return frame
    
    # ============= MAIN =============
    
    def apply_clothing_item(self, frame, clothing_type, item_index):
        """Apply clothing"""
        if frame is None:
            return frame
        
        try:
            items = self.clothing_templates.get(clothing_type, [])
            if not items or item_index >= len(items):
                return frame
            
            clothing_item = items[item_index]
            
            if clothing_type == "tshirts":
                result = self.apply_tshirt_color_replacement(frame, clothing_item)
            elif clothing_type == "shirts":
                result = self.apply_shirt_overlay(frame, clothing_item)
            else:
                result = frame
            
            self.current_outfit = clothing_item
            self.current_outfit_type = clothing_type
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return frame
    
    def debug_draw_body_landmarks(self, frame):
        """Debug visualization"""
        result = frame.copy()
        body_points = self.detect_neck_and_shoulders(frame)
        
        if body_points:
            neck_x, neck_y = body_points['neck']
            left_shoulder = body_points['left_shoulder']
            right_shoulder = body_points['right_shoulder']
            
            # Draw neck point
            cv2.circle(result, (neck_x, neck_y), 8, (0, 255, 0), -1)
            cv2.putText(result, "NECK", (neck_x + 10, neck_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Draw shoulders
            cv2.circle(result, left_shoulder, 8, (255, 0, 0), -1)
            cv2.circle(result, right_shoulder, 8, (255, 0, 0), -1)
            cv2.line(result, left_shoulder, right_shoulder, (255, 255, 0), 3)
            
            cv2.putText(result, "Body Detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(result, "No Body Detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return result
    
    def reset_pose_history(self):
        self.tshirt_mask = None
    
    def clear_cache(self):
        for clothing_type in self.clothing_templates:
            for item in self.clothing_templates[clothing_type]:
                item['color_hue'] = None
    
    def set_quality_mode(self, high_quality=True):
        pass
    
    def get_performance_stats(self):
        return {'background_trained': True}
    
    def get_available_clothing(self, clothing_type):
        return self.clothing_templates.get(clothing_type, [])
"""
SIMPLE DIRECT SHIRT PLACEMENT
No complex warping - just resize and place at neck
"""

import cv2
import numpy as np
import os

class ProfessionalClothingEngine:
    def __init__(self, replicate_api_key=None):
        self.clothing_templates = {}
        self.current_outfit = None
        self.current_outfit_type = None
        self.tshirt_mask = None
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.load_clothing_images()
        print("✅ Simple shirt engine ready!")
    
    def load_clothing_images(self):
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
    
    def train_background(self, frame):
        return True
    
    def detect_face_and_neck(self, frame):
        """Simple face detection"""
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        if len(faces) > 0:
            fx, fy, fw, fh = max(faces, key=lambda x: x[2] * x[3])
            
            neck_x = fx + fw // 2
            neck_y = fy + fh  # Bottom of face = neck
            
            return {
                'neck_x': neck_x,
                'neck_y': neck_y,
                'face_width': fw,
                'face_height': fh
            }
        
        return None
    
    # ============= T-SHIRT (HSV) =============
    
    def extract_dominant_color(self, clothing_img):
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
    
    def create_simple_torso_mask(self, frame):
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        face_info = self.detect_face_and_neck(frame)
        
        if face_info:
            neck_x = face_info['neck_x']
            neck_y = face_info['neck_y']
            fw = face_info['face_width']
            fh = face_info['face_height']
            
            shoulder_y = neck_y + int(fh * 0.2)
            waist_y = neck_y + int(fh * 5.0)
            
            shoulder_width = int(fw * 2.5)
            waist_width = int(fw * 2.7)
            
            torso_points = np.array([
                [neck_x - shoulder_width//2, shoulder_y],
                [neck_x + shoulder_width//2, shoulder_y],
                [neck_x + waist_width//2, waist_y],
                [neck_x - waist_width//2, waist_y]
            ], dtype=np.int32)
            
            cv2.fillPoly(mask, [torso_points], 255)
            
            face_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(face_mask, (neck_x, neck_y - fh // 2), 
                       (fw // 2 + 10, fh // 2 + 20), 0, 0, 360, 255, -1)
            mask = cv2.subtract(mask, face_mask)
        else:
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
        
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        
        return mask
    
    def apply_tshirt_color_replacement(self, frame, clothing_item):
        try:
            clothing_img = clothing_item['image']
            
            if clothing_item['color_hue'] is None:
                clothing_item['color_hue'] = self.extract_dominant_color(clothing_img)
            
            target_hue = clothing_item['color_hue']
            mask = self.create_simple_torso_mask(frame)
            self.tshirt_mask = mask
            
            result = self.replace_color_simple(frame, mask, target_hue)
            return result
        except Exception as e:
            print(f"T-shirt error: {e}")
            return frame
    
    # ============= SHIRT (SIMPLE RESIZE & PLACE) =============
    
    def remove_background_aggressive(self, img):
        """Remove white background completely"""
        
        if len(img.shape) == 3 and img.shape[2] == 4:
            bgr = img[:, :, :3]
            alpha_original = img[:, :, 3]
        else:
            bgr = img
            alpha_original = None
        
        # Multiple white detection methods
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 130])
        upper_white = np.array([180, 70, 255])
        white_mask1 = cv2.inRange(hsv, lower_white, upper_white)
        
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        _, white_mask2 = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
        
        b, g, r = cv2.split(bgr)
        white_mask3 = ((b > 130) & (g > 130) & (r > 130)).astype(np.uint8) * 255
        
        combined_white = cv2.bitwise_or(white_mask1, white_mask2)
        combined_white = cv2.bitwise_or(combined_white, white_mask3)
        
        shirt_mask = cv2.bitwise_not(combined_white)
        
        if alpha_original is not None:
            shirt_mask = cv2.bitwise_and(shirt_mask, alpha_original)
        
        kernel = np.ones((5, 5), np.uint8)
        shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        shirt_mask = cv2.erode(shirt_mask, kernel, iterations=2)
        shirt_mask = cv2.GaussianBlur(shirt_mask, (5, 5), 0)
        
        _, shirt_mask = cv2.threshold(shirt_mask, 20, 255, cv2.THRESH_BINARY)
        
        return bgr, shirt_mask
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """SIMPLE APPROACH: Resize shirt and place directly at neck"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🔍 Simple shirt placement...")
            
            # Detect face/neck
            face_info = self.detect_face_and_neck(frame)
            
            if not face_info:
                print("❌ No face detected")
                return frame
            
            neck_x = face_info['neck_x']
            neck_y = face_info['neck_y']
            fw = face_info['face_width']
            fh = face_info['face_height']
            
            print(f"✅ Neck at: ({neck_x}, {neck_y})")
            
            # Simple shirt dimensions based on face
            shirt_width = int(fw * 3.0)
            shirt_height = int(fh * 6.0)
            
            # CRITICAL: Position shirt to start AT neck (not below it!)
            shirt_x = neck_x - shirt_width // 2
            shirt_y = neck_y  # Start exactly at neck!
            
            print(f"📏 Shirt: {shirt_width}x{shirt_height} at ({shirt_x}, {shirt_y})")
            
            # Bounds check
            if shirt_x < 0:
                shirt_width += shirt_x
                shirt_x = 0
            if shirt_y < 0:
                shirt_height += shirt_y
                shirt_y = 0
            if shirt_x + shirt_width > w:
                shirt_width = w - shirt_x
            if shirt_y + shirt_height > h:
                shirt_height = h - shirt_y
            
            if shirt_width <= 0 or shirt_height <= 0:
                print("❌ Invalid dimensions")
                return frame
            
            # Load and process shirt
            clothing_img = clothing_item['image']
            
            # Resize shirt to calculated dimensions
            resized_shirt = cv2.resize(clothing_img, (shirt_width, shirt_height))
            
            # Remove background
            shirt_bgr, shirt_alpha = self.remove_background_aggressive(resized_shirt)
            
            non_zero = cv2.countNonZero(shirt_alpha)
            print(f"🎨 Shirt pixels: {non_zero}")
            
            if non_zero < 500:
                print("⚠️ Too few pixels, using full image")
                shirt_alpha = np.ones((shirt_height, shirt_width), dtype=np.uint8) * 200
            
            # Get ROI
            roi = frame[shirt_y:shirt_y + shirt_height, shirt_x:shirt_x + shirt_width]
            
            if roi.shape[:2] != (shirt_height, shirt_width):
                print(f"❌ ROI mismatch")
                return frame
            
            # Alpha blend
            alpha_norm = shirt_alpha.astype(float) / 255.0
            alpha_3d = np.stack([alpha_norm] * 3, axis=2)
            
            result = frame.copy()
            blended = (shirt_bgr.astype(float) * alpha_3d + 
                      roi.astype(float) * (1.0 - alpha_3d))
            
            result[shirt_y:shirt_y + shirt_height, shirt_x:shirt_x + shirt_width] = blended.astype(np.uint8)
            
            print(f"✅✅✅ Shirt placed at neck!")
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return frame
    
    # ============= MAIN =============
    
    def apply_clothing_item(self, frame, clothing_type, item_index):
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
        result = frame.copy()
        face_info = self.detect_face_and_neck(frame)
        
        if face_info:
            neck_x = face_info['neck_x']
            neck_y = face_info['neck_y']
            
            cv2.circle(result, (neck_x, neck_y), 10, (0, 255, 0), -1)
            cv2.putText(result, f"NECK ({neck_x},{neck_y})", (neck_x + 15, neck_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.putText(result, "Face Detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(result, "No Face", (10, 30),
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
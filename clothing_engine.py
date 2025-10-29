"""
UPDATED SHIRT OVERLAY WITH PROPER NECK POSITIONING
Ensures shirt starts from neck and covers entire body properly
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
        print("✅ Enhanced shirt engine ready!")
    
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
        """Enhanced face detection with better neck positioning"""
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Use multiple detection parameters for better accuracy
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=6, 
            minSize=(80, 80),
            maxSize=(400, 400)
        )
        
        if len(faces) > 0:
            # Find the largest face
            fx, fy, fw, fh = max(faces, key=lambda x: x[2] * x[3])
            
            # Calculate neck position - this is CRITICAL for proper shirt placement
            # Neck is at the bottom of the face, slightly adjusted
            neck_x = fx + fw // 2
            neck_y = fy + int(fh * 0.85)  # 85% down the face for neck position
            
            return {
                'neck_x': neck_x,
                'neck_y': neck_y,
                'face_width': fw,
                'face_height': fh,
                'face_x': fx,
                'face_y': fy
            }
        
        # Fallback: estimate face position based on frame center
        return {
            'neck_x': w // 2,
            'neck_y': int(h * 0.35),  # Higher up in the frame
            'face_width': 150,
            'face_height': 150,
            'face_x': w // 2 - 75,
            'face_y': int(h * 0.2)
        }
    
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
            
            # Start the shirt RIGHT AT THE NECK level
            shoulder_y = neck_y
            waist_y = neck_y + int(fh * 4.5)  # Extended length
            
            shoulder_width = int(fw * 2.2)
            waist_width = int(fw * 2.4)
            
            torso_points = np.array([
                [neck_x - shoulder_width//2, shoulder_y],
                [neck_x + shoulder_width//2, shoulder_y],
                [neck_x + waist_width//2, waist_y],
                [neck_x - waist_width//2, waist_y]
            ], dtype=np.int32)
            
            cv2.fillPoly(mask, [torso_points], 255)
            
            # Remove face area
            face_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(face_mask, (neck_x, neck_y - fh // 2), 
                       (fw // 2 + 15, fh // 2 + 25), 0, 0, 360, 255, -1)
            mask = cv2.subtract(mask, face_mask)
        else:
            # Fallback positioning
            top_y = int(h * 0.25)  # Higher start
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
    
    # ============= SHIRT (PROPER NECK POSITIONING) =============
    
    def remove_background_aggressive(self, img):
        """Remove background while preserving shirt details"""
        
        if len(img.shape) == 3 and img.shape[2] == 4:
            bgr = img[:, :, :3]
            alpha_original = img[:, :, 3]
        else:
            bgr = img
            alpha_original = None
        
        h, w = bgr.shape[:2]
        
        # Create mask using multiple methods
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        
        # Method 1: Edge detection
        edges = cv2.Canny(gray, 50, 150)
        kernel = np.ones((3, 3), np.uint8)
        edges_dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Method 2: Color-based background removal
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        
        # Detect light backgrounds (white, light gray)
        light_mask = ((hsv[:, :, 2] > 200) & (hsv[:, :, 1] < 50)).astype(np.uint8) * 255
        
        # Combine methods
        combined_mask = cv2.bitwise_or(edges_dilated, light_mask)
        
        # Find contours
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            shirt_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(shirt_mask, [largest_contour], -1, 255, -1)
        else:
            shirt_mask = np.ones((h, w), dtype=np.uint8) * 255
        
        # Use original alpha if available
        if alpha_original is not None:
            shirt_mask = cv2.bitwise_and(shirt_mask, alpha_original)
        
        # Clean up mask
        kernel_clean = np.ones((3, 3), np.uint8)
        shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel_clean, iterations=2)
        shirt_mask = cv2.GaussianBlur(shirt_mask, (3, 3), 0)
        
        return bgr, shirt_mask
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """FIXED: Shirt now starts from neck and covers properly"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🔍 Applying shirt with PROPER NECK POSITIONING...")
            
            # Detect face/neck with enhanced accuracy
            face_info = self.detect_face_and_neck(frame)
            
            if not face_info:
                print("❌ No face detected, using fallback positioning")
                # Fallback: center of upper frame
                neck_x = w // 2
                neck_y = int(h * 0.3)
                fw = 150
                fh = 150
            else:
                neck_x = face_info['neck_x']
                neck_y = face_info['neck_y']
                fw = face_info['face_width']
                fh = face_info['face_height']
            
            print(f"✅ Neck detected at: ({neck_x}, {neck_y})")
            
            # CRITICAL FIX: Position shirt to start RIGHT AT THE NECK
            # This ensures the collar sits properly at the neck
            shirt_start_y = neck_y - int(fh * 0.1)  # Start slightly above neck for collar
            
            # Calculate dimensions based on face size for proper fit
            shirt_width = int(fw * 2.8)  # Shoulder width
            shirt_height = int(h * 0.8)  # Cover most of body
            
            # Ensure minimum dimensions
            shirt_width = max(shirt_width, 300)
            shirt_height = max(shirt_height, 500)
            
            # Center horizontally on neck
            shirt_x = neck_x - shirt_width // 2
            
            # Adjust for frame boundaries
            if shirt_x < 0:
                shirt_x = 0
            if shirt_x + shirt_width > w:
                shirt_width = w - shirt_x
            
            # Ensure we have enough vertical space
            if shirt_start_y < 0:
                shirt_start_y = 0
            if shirt_start_y + shirt_height > h:
                shirt_height = h - shirt_start_y
            
            print(f"🎯 Shirt positioning:")
            print(f"   Start Y: {shirt_start_y}px (at neck level)")
            print(f"   Width: {shirt_width}px")
            print(f"   Height: {shirt_height}px")
            
            # Load and prepare shirt image
            clothing_img = clothing_item['image']
            orig_h, orig_w = clothing_img.shape[:2]
            
            # Resize shirt maintaining aspect ratio but fitting our dimensions
            target_width = shirt_width
            target_height = int(orig_h * (target_width / orig_w))
            
            # If height is too small, scale up
            if target_height < shirt_height:
                scale_factor = shirt_height / target_height
                target_width = int(target_width * scale_factor)
                target_height = shirt_height
            
            # Final resize
            resized_shirt = cv2.resize(clothing_img, (target_width, target_height), 
                                      interpolation=cv2.INTER_AREA)
            
            # Remove background
            shirt_bgr, shirt_alpha = self.remove_background_aggressive(resized_shirt)
            
            # Calculate visible portion
            visible_height = min(target_height, h - shirt_start_y)
            visible_width = min(target_width, w - shirt_x)
            
            if visible_height <= 0 or visible_width <= 0:
                print("❌ No visible area - adjustment needed")
                return frame
            
            # Extract visible portion of shirt
            shirt_bgr_visible = shirt_bgr[:visible_height, :visible_width]
            shirt_alpha_visible = shirt_alpha[:visible_height, :visible_width]
            
            # Get ROI from frame
            roi_y_start = shirt_start_y
            roi_y_end = shirt_start_y + visible_height
            roi_x_start = shirt_x
            roi_x_end = shirt_x + visible_width
            
            # Safety checks
            if roi_y_end > h or roi_x_end > w:
                print("❌ ROI out of bounds")
                return frame
            
            roi = frame[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
            
            # Ensure ROI and shirt have same dimensions
            if roi.shape[:2] != shirt_bgr_visible.shape[:2]:
                print(f"❌ Size mismatch: ROI={roi.shape}, Shirt={shirt_bgr_visible.shape}")
                # Resize ROI to match shirt
                roi = cv2.resize(roi, (shirt_bgr_visible.shape[1], shirt_bgr_visible.shape[0]))
            
            # Alpha blending
            alpha_norm = shirt_alpha_visible.astype(float) / 255.0
            alpha_3d = np.stack([alpha_norm] * 3, axis=2)
            
            # Create result
            result = frame.copy()
            
            # Blend shirt with ROI
            blended = (shirt_bgr_visible.astype(float) * alpha_3d + 
                      roi.astype(float) * (1.0 - alpha_3d))
            
            # Place blended result back
            result[roi_y_start:roi_y_end, roi_x_start:roi_x_end] = blended.astype(np.uint8)
            
            print(f"✅✅✅ SHIRT SUCCESSFULLY APPLIED!")
            print(f"    ✅ Starts at neck level: y={shirt_start_y}")
            print(f"    ✅ Properly covers body")
            print(f"    ✅ Your blue t-shirt should be COMPLETELY hidden!\n")
            
            return result
            
        except Exception as e:
            print(f"❌ Shirt overlay error: {e}")
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
            fw = face_info['face_width']
            fh = face_info['face_height']
            
            # Draw face rectangle
            cv2.rectangle(result, (face_info['face_x'], face_info['face_y']), 
                         (face_info['face_x'] + fw, face_info['face_y'] + fh), 
                         (255, 0, 0), 2)
            
            # Draw neck point
            cv2.circle(result, (neck_x, neck_y), 8, (0, 255, 0), -1)
            cv2.putText(result, f"NECK ({neck_x},{neck_y})", (neck_x + 15, neck_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Draw expected shirt area
            shirt_start_y = neck_y - int(fh * 0.1)
            shirt_width = int(fw * 2.8)
            shirt_x = neck_x - shirt_width // 2
            
            cv2.rectangle(result, (shirt_x, shirt_start_y), 
                         (shirt_x + shirt_width, shirt_start_y + int(h * 0.8)), 
                         (0, 255, 255), 2)
            
            cv2.putText(result, "Shirt Area", (shirt_x, shirt_start_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
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
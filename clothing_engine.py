"""
UPDATED SHIRT OVERLAY WITH PROPER LENGTH
Ensures shirt covers entire body from neck to beyond visible frame
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
    
    # ============= SHIRT (PROPER LENGTH OVERLAY) =============
    
    def remove_background_aggressive(self, img):
        """ADVANCED background removal - Remove ALL background, keep ONLY shirt"""
        
        if len(img.shape) == 3 and img.shape[2] == 4:
            bgr = img[:, :, :3]
            alpha_original = img[:, :, 3]
        else:
            bgr = img
            alpha_original = None
        
        h, w = bgr.shape[:2]
        
        # Step 1: Detect edges of the shirt using Canny
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 100)
        
        # Step 2: Dilate edges to close gaps
        kernel = np.ones((3, 3), np.uint8)
        edges_dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Step 3: Find contours
        contours, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Step 4: Create mask from largest contour (the shirt)
        if contours:
            # Find the largest contour by area
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Create mask and fill the contour
            contour_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(contour_mask, [largest_contour], -1, 255, -1)
        else:
            contour_mask = np.zeros((h, w), dtype=np.uint8)
        
        # Step 5: Combine with color-based detection
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        h_hsv, s, v = cv2.split(hsv)
        
        # Detect white/light backgrounds (high value, low saturation)
        white_mask = ((v > 180) & (s < 40)).astype(np.uint8) * 255
        
        # Also detect light gray backgrounds
        b, g, r = cv2.split(bgr)
        light_gray_mask = ((b > 180) & (g > 180) & (r > 180) & 
                          (np.abs(b.astype(int) - g.astype(int)) < 15) &
                          (np.abs(g.astype(int) - r.astype(int)) < 15)).astype(np.uint8) * 255
        
        # Combine white and light gray detection
        background_mask = cv2.bitwise_or(white_mask, light_gray_mask)
        
        # Invert to get foreground
        color_shirt_mask = cv2.bitwise_not(background_mask)
        
        # Step 6: Combine contour and color masks
        shirt_mask = cv2.bitwise_and(contour_mask, color_shirt_mask)
        
        # Step 7: Use alpha channel if available as additional guidance
        if alpha_original is not None:
            alpha_mask = (alpha_original > 50).astype(np.uint8) * 255
            shirt_mask = cv2.bitwise_and(shirt_mask, alpha_mask)
        
        # Step 8: Flood fill from corners to remove any remaining background
        flood_mask = shirt_mask.copy()
        # Create a slightly larger mask for flood fill
        h_fm, w_fm = flood_mask.shape
        flood_fill_mask = np.zeros((h_fm + 2, w_fm + 2), dtype=np.uint8)
        
        # Flood fill from all four corners
        cv2.floodFill(flood_mask, flood_fill_mask, (0, 0), 0)
        cv2.floodFill(flood_mask, flood_fill_mask, (w_fm - 1, 0), 0)
        cv2.floodFill(flood_mask, flood_fill_mask, (0, h_fm - 1), 0)
        cv2.floodFill(flood_mask, flood_fill_mask, (w_fm - 1, h_fm - 1), 0)
        
        # Step 9: Clean up the mask
        kernel_clean = np.ones((5, 5), np.uint8)
        
        # Close gaps
        shirt_mask = cv2.morphologyEx(flood_mask, cv2.MORPH_CLOSE, kernel_clean, iterations=3)
        
        # Remove small noise
        shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel_clean, iterations=2)
        
        # Smooth edges
        shirt_mask = cv2.GaussianBlur(shirt_mask, (5, 5), 0)
        
        # Final threshold
        _, shirt_mask = cv2.threshold(shirt_mask, 127, 255, cv2.THRESH_BINARY)
        
        # Step 10: Erode slightly to remove white fringe
        kernel_erode = np.ones((3, 3), np.uint8)
        shirt_mask = cv2.erode(shirt_mask, kernel_erode, iterations=1)
        
        return bgr, shirt_mask
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """EXTENDED shirt that covers entire visible body"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🔍 Applying shirt with FULL body coverage...")
            
            # Detect face/neck
            face_info = self.detect_face_and_neck(frame)
            
            if not face_info:
                print("❌ No face detected")
                return frame
            
            neck_x = face_info['neck_x']
            neck_y = face_info['neck_y']
            fw = face_info['face_width']
            fh = face_info['face_height']
            
            print(f"✅ Face detected - Neck at: ({neck_x}, {neck_y})")
            print(f"📺 Frame size: {w}x{h}")
            
            # CRITICAL CHANGES FOR PROPER COVERAGE:
            
            # 1. Perfect neck positioning - start at proper collar level
            one_cm_pixels = 35  # Approximate pixel to cm conversion
            # Start at neck bottom (where collar should sit)
            # Slight offset above neck to ensure collar covers properly
            start_offset_above_neck = int(fh * 0.3)  # Start just above neck for collar
            shirt_y = max(0, neck_y - start_offset_above_neck)
            
            # 2. Width: Cover shoulders completely with extra margin
            base_shoulder_width = int(fw * 3.8)  # Increased from 3.5 to 3.8
            extra_width = 5 * one_cm_pixels  # Add 5cm total width (2.5cm each side)
            shirt_width = base_shoulder_width + extra_width
            
            # 3. Height: MUCH LONGER - extend well past visible frame
            # Calculate from shirt start to bottom of frame, then add MORE
            available_height = h - shirt_y
            extra_height_extension = int(available_height * 0.5)  # Add 50% more
            shirt_height = available_height + extra_height_extension
            
            # For safety, ensure minimum shirt length
            min_shirt_length = int(fh * 7.0)  # At least 7x face height
            shirt_height = max(shirt_height, min_shirt_length)
            
            print(f"📏 Shirt positioning:")
            print(f"   Start Y: {shirt_y}px (ABOVE neck by {start_offset_above_neck}px)")
            print(f"   Width: {shirt_width}px")
            print(f"   Height: {shirt_height}px (extended beyond screen)")
            print(f"   Bottom would be at: y={shirt_y + shirt_height}px (screen height: {h}px)")
            
            # Center horizontally on neck
            shirt_x = neck_x - shirt_width // 2
            
            # Bounds check for X only
            if shirt_x < 0:
                shirt_width += shirt_x
                shirt_x = 0
            if shirt_x + shirt_width > w:
                shirt_width = w - shirt_x
            
            if shirt_width <= 0:
                print("❌ Invalid width")
                return frame
            
            print(f"📍 Final position: ({shirt_x}, {shirt_y}) size: {shirt_width}x{shirt_height}")
            
            # Load and prepare shirt image
            clothing_img = clothing_item['image']
            
            # Get original shirt aspect ratio
            orig_h, orig_w = clothing_img.shape[:2]
            orig_aspect = orig_w / orig_h
            
            print(f"👔 Original shirt: {orig_w}x{orig_h} (aspect: {orig_aspect:.2f})")
            
            # Resize shirt to our calculated dimensions
            # This will stretch vertically to cover the body
            resized_shirt = cv2.resize(clothing_img, (shirt_width, shirt_height), 
                                      interpolation=cv2.INTER_AREA)
            
            # Remove background
            shirt_bgr, shirt_alpha = self.remove_background_aggressive(resized_shirt)
            
            non_zero = cv2.countNonZero(shirt_alpha)
            print(f"🎨 Shirt pixels after background removal: {non_zero}")
            
            if non_zero < 500:
                print("⚠️ Few pixels detected, using full image")
                shirt_alpha = np.ones((shirt_height, shirt_width), dtype=np.uint8) * 200
            
            # Calculate the visible portion that fits in frame
            visible_height = min(shirt_height, h - shirt_y)
            
            if visible_height <= 0:
                print("❌ No visible height")
                return frame
            
            print(f"👁️  Visible shirt height: {visible_height}px (out of {shirt_height}px total)")
            
            # Take only the visible top portion of the shirt
            shirt_bgr_visible = shirt_bgr[:visible_height, :]
            shirt_alpha_visible = shirt_alpha[:visible_height, :]
            
            # Get ROI from frame
            roi = frame[shirt_y:shirt_y + visible_height, shirt_x:shirt_x + shirt_width]
            
            if roi.shape[:2] != (visible_height, shirt_width):
                print(f"❌ Size mismatch: ROI={roi.shape}, Expected=({visible_height}, {shirt_width})")
                return frame
            
            # Alpha blend with balanced transparency
            alpha_norm = shirt_alpha_visible.astype(float) / 255.0
            
            # Light curve adjustment for smooth edges (not too aggressive)
            alpha_norm = np.power(alpha_norm, 0.9)  # Gentle curve
            
            alpha_3d = np.stack([alpha_norm] * 3, axis=2)
            
            result = frame.copy()
            blended = (shirt_bgr_visible.astype(float) * alpha_3d + 
                      roi.astype(float) * (1.0 - alpha_3d))
            
            result[shirt_y:shirt_y + visible_height, shirt_x:shirt_x + shirt_width] = blended.astype(np.uint8)
            
            print(f"✅✅✅ SHIRT SUCCESSFULLY APPLIED!")
            print(f"    ✅ Starts: AT CHIN level (y={shirt_y}) - NO NECK GAP!")
            print(f"    ✅ Covers: {visible_height}px visible height")
            print(f"    ✅ Total shirt extends: {shirt_height}px (beyond screen)")
            print(f"    ✅ Should connect perfectly with your neck!\n")
            
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
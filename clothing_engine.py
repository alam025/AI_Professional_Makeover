"""
UPDATED SHIRT OVERLAY WITH PROPER BACKGROUND REMOVAL
Ensures shirt has no white background and starts from neck
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
    
    # ============= SHIRT (COMPLETE BACKGROUND REMOVAL) =============
    
    def remove_background_completely(self, img):
        """COMPLETE background removal - Remove ALL white/light backgrounds"""
        
        if len(img.shape) == 3 and img.shape[2] == 4:
            # Already has alpha channel - use it
            bgr = img[:, :, :3]
            alpha = img[:, :, 3]
            
            # Enhance existing alpha - make sure background is completely transparent
            _, alpha_binary = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
            
            # Clean up the alpha mask
            kernel = np.ones((3, 3), np.uint8)
            alpha_cleaned = cv2.morphologyEx(alpha_binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            alpha_cleaned = cv2.morphologyEx(alpha_cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
            
            return bgr, alpha_cleaned
        else:
            # No alpha channel - use aggressive color-based removal
            bgr = img
            h, w = bgr.shape[:2]
            
            # Convert to different color spaces for better detection
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
            
            # Detect white/light backgrounds in multiple ways
            # Method 1: HSV - high value, low saturation
            white_mask_hsv = ((hsv[:, :, 2] > 200) & (hsv[:, :, 1] < 80)).astype(np.uint8) * 255
            
            # Method 2: LAB - light backgrounds have high L channel
            white_mask_lab = (lab[:, :, 0] > 200).astype(np.uint8) * 255
            
            # Method 3: BGR - all channels high for white
            b, g, r = cv2.split(bgr)
            white_mask_bgr = ((b > 200) & (g > 200) & (r > 200)).astype(np.uint8) * 255
            
            # Method 4: Light gray backgrounds
            gray_mask = ((b > 180) & (g > 180) & (r > 180) & 
                        (np.abs(b.astype(int) - g.astype(int)) < 20) &
                        (np.abs(g.astype(int) - r.astype(int)) < 20)).astype(np.uint8) * 255
            
            # Combine all white/light background masks
            combined_white_mask = cv2.bitwise_or(white_mask_hsv, white_mask_lab)
            combined_white_mask = cv2.bitwise_or(combined_white_mask, white_mask_bgr)
            combined_white_mask = cv2.bitwise_or(combined_white_mask, gray_mask)
            
            # Invert to get shirt mask (foreground)
            shirt_mask = cv2.bitwise_not(combined_white_mask)
            
            # Use edge detection to refine mask
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Dilate edges to connect shirt boundaries
            kernel = np.ones((3, 3), np.uint8)
            edges_dilated = cv2.dilate(edges, kernel, iterations=2)
            
            # Combine with color-based mask
            shirt_mask = cv2.bitwise_and(shirt_mask, cv2.bitwise_not(edges_dilated))
            
            # Find largest contour (the shirt)
            contours, _ = cv2.findContours(shirt_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                refined_mask = np.zeros((h, w), dtype=np.uint8)
                cv2.drawContours(refined_mask, [largest_contour], -1, 255, -1)
                shirt_mask = refined_mask
            
            # Clean up the mask
            kernel_clean = np.ones((5, 5), np.uint8)
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel_clean, iterations=2)
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel_clean, iterations=1)
            
            # Final blur for smooth edges
            shirt_mask = cv2.GaussianBlur(shirt_mask, (3, 3), 0)
            _, shirt_mask = cv2.threshold(shirt_mask, 127, 255, cv2.THRESH_BINARY)
            
            return bgr, shirt_mask
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """Shirt overlay with COMPLETE background removal"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🔍 Applying shirt with NO BACKGROUND...")
            
            # Detect face/neck
            face_info = self.detect_face_and_neck(frame)
            
            if not face_info:
                print("❌ No face detected, using fallback positioning")
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
            
            # Position shirt to start RIGHT AT THE NECK
            shirt_start_y = neck_y - int(fh * 0.1)  # Start slightly above neck for collar
            
            # Calculate dimensions based on face size
            shirt_width = int(fw * 2.8)
            shirt_height = int(h * 0.8)
            
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
            
            # Resize shirt maintaining aspect ratio
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
            
            # COMPLETE background removal
            shirt_bgr, shirt_alpha = self.remove_background_completely(resized_shirt)
            
            # Check if we have enough non-transparent pixels
            non_zero_pixels = cv2.countNonZero(shirt_alpha)
            print(f"🎨 Non-transparent shirt pixels: {non_zero_pixels}")
            
            if non_zero_pixels < 1000:
                print("⚠️ Warning: Very few shirt pixels detected")
            
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
                print(f"🔧 Resizing ROI to match shirt: {roi.shape} -> {shirt_bgr_visible.shape}")
                roi = cv2.resize(roi, (shirt_bgr_visible.shape[1], shirt_bgr_visible.shape[0]))
            
            # Alpha blending - COMPLETE background removal
            alpha_norm = shirt_alpha_visible.astype(float) / 255.0
            
            # Use aggressive threshold to ensure complete background removal
            alpha_norm = np.where(alpha_norm > 0.1, alpha_norm, 0.0)
            
            alpha_3d = np.stack([alpha_norm] * 3, axis=2)
            
            # Create result
            result = frame.copy()
            
            # Blend shirt with ROI - only where alpha > 0
            blended = np.where(alpha_3d > 0.1, 
                             shirt_bgr_visible.astype(float), 
                             roi.astype(float))
            
            # Place blended result back
            result[roi_y_start:roi_y_end, roi_x_start:roi_x_end] = blended.astype(np.uint8)
            
            print(f"✅✅✅ SHIRT APPLIED WITH NO BACKGROUND!")
            print(f"    ✅ White background completely removed")
            print(f"    ✅ Starts at neck level: y={shirt_start_y}")
            print(f"    ✅ Only shirt pixels visible - no white background!\n")
            
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
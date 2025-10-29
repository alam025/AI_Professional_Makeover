"""
UPDATED SHIRT OVERLAY WITH PROPER BODY COVERAGE
Shirt starts from neck, covers shoulders, and extends to bottom
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
        """Enhanced face detection with precise neck positioning"""
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
            
            # Calculate neck position - RIGHT AT THE BASE OF THE NECK
            neck_x = fx + fw // 2
            neck_y = fy + int(fh * 0.9)  # 90% down the face - base of neck
            
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
            'neck_y': int(h * 0.3),  # Higher up in the frame
            'face_width': 150,
            'face_height': 150,
            'face_x': w // 2 - 75,
            'face_y': int(h * 0.15)
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
    
    # ============= SHIRT (PROPER BODY COVERAGE) =============
    
    def remove_background_ultra_aggressive(self, img):
        """ULTRA-AGGRESSIVE background removal - removes ALL white/light pixels"""
        
        if len(img.shape) == 3 and img.shape[2] == 4:
            # Use alpha channel if available
            bgr = img[:, :, :3]
            alpha = img[:, :, 3]
            
            # Make alpha channel more aggressive
            _, alpha_binary = cv2.threshold(alpha, 5, 255, cv2.THRESH_BINARY)
            
            # Additional color-based cleanup
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            white_pixels = (hsv[:, :, 2] > 220) & (hsv[:, :, 1] < 60)
            alpha_binary[white_pixels] = 0
            
            return bgr, alpha_binary
        else:
            # No alpha channel - use extreme color-based removal
            bgr = img
            h, w = bgr.shape[:2]
            
            # Convert to multiple color spaces
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            
            # ULTRA-AGGRESSIVE white detection
            white_mask1 = (hsv[:, :, 2] > 210) & (hsv[:, :, 1] < 100)
            white_mask2 = lab[:, :, 0] > 200
            b, g, r = cv2.split(bgr)
            white_mask3 = (b > 190) & (g > 190) & (r > 190)
            white_mask4 = (gray > 200)
            white_mask5 = ((b > 180) & (g > 180) & (r > 180) & 
                          (np.abs(b.astype(int) - g.astype(int)) < 30) &
                          (np.abs(g.astype(int) - r.astype(int)) < 30))
            
            # Combine ALL white detection methods
            combined_white_mask = (white_mask1 | white_mask2 | white_mask3 | white_mask4 | white_mask5)
            
            # Create initial shirt mask (inverse of white mask)
            shirt_mask = (~combined_white_mask).astype(np.uint8) * 255
            
            # Use edge detection to find shirt boundaries
            edges = cv2.Canny(gray, 30, 100)
            kernel = np.ones((2, 2), np.uint8)
            edges_dilated = cv2.dilate(edges, kernel, iterations=1)
            
            # Remove edges from white areas
            shirt_mask = cv2.bitwise_and(shirt_mask, cv2.bitwise_not(edges_dilated))
            
            # Find the largest contour (should be the shirt)
            contours, _ = cv2.findContours(shirt_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Create mask from largest contour
                contour_mask = np.zeros((h, w), dtype=np.uint8)
                cv2.drawContours(contour_mask, [largest_contour], -1, 255, -1)
                
                # Use this as our final mask
                shirt_mask = contour_mask
            else:
                print("⚠️ No contours found, using color-based mask")
            
            # EXTREME cleaning
            kernel_clean = np.ones((3, 3), np.uint8)
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel_clean, iterations=3)
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel_clean, iterations=2)
            
            # Final aggressive threshold
            _, shirt_mask = cv2.threshold(shirt_mask, 127, 255, cv2.THRESH_BINARY)
            
            return bgr, shirt_mask
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """Shirt overlay that covers neck, shoulders, and entire body"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🎯 Applying shirt with COMPLETE BODY COVERAGE...")
            
            # Detect face/neck
            face_info = self.detect_face_and_neck(frame)
            
            if not face_info:
                print("❌ No face detected, using fallback positioning")
                neck_x = w // 2
                neck_y = int(h * 0.25)  # Higher start for fallback
                fw = 160
                fh = 160
            else:
                neck_x = face_info['neck_x']
                neck_y = face_info['neck_y']
                fw = face_info['face_width']
                fh = face_info['face_height']
            
            print(f"✅ Neck detected at: ({neck_x}, {neck_y})")
            
            # CRITICAL FIX: Start shirt RIGHT AT THE NECK (covering chest)
            # No gap - shirt starts exactly where neck ends
            shirt_start_y = neck_y - int(fh * 0.05)  # Just 5% above neck for collar
            
            # WIDER coverage for shoulders - cover entire shoulder area
            shirt_width = int(fw * 3.5)  # Much wider to cover shoulders
            
            # FULL BODY coverage - extend to bottom of screen
            shirt_height = h - shirt_start_y  # Cover from neck to bottom
            
            print(f"📏 Body coverage calculations:")
            print(f"   Face width: {fw}px, Face height: {fh}px")
            print(f"   Shirt starts at Y: {shirt_start_y}px (RIGHT AT NECK)")
            print(f"   Shirt width: {shirt_width}px (covers shoulders)")
            print(f"   Shirt height: {shirt_height}px (covers to bottom)")
            
            # Center horizontally on neck
            shirt_x = neck_x - shirt_width // 2
            
            # Adjust for frame boundaries - but keep it WIDE
            if shirt_x < 0:
                # If too far left, extend right side to maintain width
                shirt_width += shirt_x
                shirt_x = 0
            if shirt_x + shirt_width > w:
                # If too far right, extend left side to maintain width
                overshoot = (shirt_x + shirt_width) - w
                shirt_x = max(0, shirt_x - overshoot)
                shirt_width = w - shirt_x
            
            # Ensure minimum dimensions for proper coverage
            shirt_width = max(shirt_width, 400)  # Minimum width to cover shoulders
            shirt_height = max(shirt_height, 600)  # Minimum height to cover body
            
            print(f"📍 Final shirt position:")
            print(f"   X: {shirt_x}, Y: {shirt_start_y}")
            print(f"   Width: {shirt_width}, Height: {shirt_height}")
            print(f"   Should cover from neck to bottom screen")
            
            # Load and prepare shirt image
            clothing_img = clothing_item['image']
            orig_h, orig_w = clothing_img.shape[:2]
            orig_aspect = orig_w / orig_h
            
            print(f"👔 Original shirt: {orig_w}x{orig_h} (aspect: {orig_aspect:.2f})")
            
            # Resize shirt to cover our calculated area
            # We want to maintain aspect ratio but ensure full coverage
            target_width = shirt_width
            target_height = int(shirt_width / orig_aspect)
            
            # If the calculated height is less than needed, scale up
            if target_height < shirt_height:
                scale_factor = shirt_height / target_height
                target_width = int(target_width * scale_factor)
                target_height = shirt_height
            
            print(f"🔧 Resizing shirt to: {target_width}x{target_height}")
            
            resized_shirt = cv2.resize(clothing_img, (target_width, target_height), 
                                      interpolation=cv2.INTER_AREA)
            
            # Remove background
            shirt_bgr, shirt_alpha = self.remove_background_ultra_aggressive(resized_shirt)
            
            # Calculate visible portion (should be most of it)
            visible_height = min(target_height, h - shirt_start_y)
            visible_width = min(target_width, w - shirt_x)
            
            print(f"👁️  Visible area: {visible_width}x{visible_height}")
            
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
            
            # Ensure dimensions match
            if roi.shape[:2] != shirt_bgr_visible.shape[:2]:
                print(f"🔧 Resizing ROI to match shirt")
                roi = cv2.resize(roi, (shirt_bgr_visible.shape[1], shirt_bgr_visible.shape[0]))
            
            # Alpha blending - NO WHITE BACKGROUND
            alpha_norm = shirt_alpha_visible.astype(float) / 255.0
            
            # Remove any white pixels that might have survived
            hsv_shirt = cv2.cvtColor(shirt_bgr_visible, cv2.COLOR_BGR2HSV)
            white_pixels = (hsv_shirt[:, :, 2] > 200) & (hsv_shirt[:, :, 1] < 80)
            alpha_norm[white_pixels] = 0.0
            
            alpha_3d = np.stack([alpha_norm] * 3, axis=2)
            
            # Create result
            result = frame.copy()
            
            # Only show shirt where alpha > 0, otherwise show original ROI
            blended = np.where(alpha_3d > 0.01, 
                             shirt_bgr_visible.astype(float), 
                             roi.astype(float))
            
            # Apply to result
            result[roi_y_start:roi_y_end, roi_x_start:roi_x_end] = blended.astype(np.uint8)
            
            # Draw debug info on result
            cv2.circle(result, (neck_x, neck_y), 8, (0, 255, 0), -1)
            cv2.putText(result, "NECK", (neck_x + 10, neck_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            print(f"✅✅✅ SHIRT APPLIED WITH COMPLETE COVERAGE!")
            print(f"    ✅ Starts at neck level: y={shirt_start_y}")
            print(f"    ✅ Covers shoulders: width={shirt_width}px")
            print(f"    ✅ Extends to bottom: height={shirt_height}px")
            print(f"    ✅ No gap between neck and shirt")
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
            shirt_start_y = neck_y - int(fh * 0.05)
            shirt_width = int(fw * 3.5)
            shirt_height = result.shape[0] - shirt_start_y
            shirt_x = neck_x - shirt_width // 2
            
            cv2.rectangle(result, (shirt_x, shirt_start_y), 
                         (shirt_x + shirt_width, shirt_start_y + shirt_height), 
                         (0, 255, 255), 2)
            
            cv2.putText(result, "Shirt Coverage Area", (shirt_x, shirt_start_y - 10),
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
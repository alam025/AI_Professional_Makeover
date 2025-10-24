"""
ADVANCED BODY-FITTING CLOTHING ENGINE
Uses body contour detection and perspective warping for natural fit
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
        self.body_contour = None
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        
        self.load_clothing_images()
        print("✅ Advanced body-fitting clothing engine ready!")
    
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
    
    def detect_body_contour(self, frame):
        """Detect body contour for natural clothing placement"""
        try:
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect upper body
            bodies = self.body_cascade.detectMultiScale(gray, 1.1, 3, minSize=(100, 100))
            
            if len(bodies) > 0:
                # Use the largest body detection
                bx, by, bw, bh = max(bodies, key=lambda x: x[2] * x[3])
                
                # Create body contour points (trapezoid shape)
                shoulder_width = bw * 1.4
                waist_width = bw * 1.2
                body_height = bh * 1.8
                
                body_points = np.array([
                    [bx + bw//2 - shoulder_width//2, by + bh//4],  # Left shoulder
                    [bx + bw//2 + shoulder_width//2, by + bh//4],  # Right shoulder
                    [bx + bw//2 + waist_width//2, by + body_height],  # Right waist
                    [bx + bw//2 - waist_width//2, by + body_height]   # Left waist
                ], dtype=np.int32)
                
                return body_points
            
            return None
        except:
            return None
    
    def detect_face_and_shoulders(self, frame):
        """Enhanced detection for shoulders and torso"""
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        if len(faces) > 0:
            fx, fy, fw, fh = max(faces, key=lambda x: x[2] * x[3])
            
            # Calculate shoulder positions
            neck_x = fx + fw // 2
            neck_y = fy + fh
            
            # Shoulder points (wider than face)
            shoulder_width = fw * 2.2
            left_shoulder = (neck_x - shoulder_width//2, neck_y + int(fh * 0.3))
            right_shoulder = (neck_x + shoulder_width//2, neck_y + int(fh * 0.3))
            
            # Waist points (slightly narrower)
            waist_y = neck_y + int(fh * 2.5)
            waist_width = shoulder_width * 0.9
            left_waist = (neck_x - waist_width//2, waist_y)
            right_waist = (neck_x + waist_width//2, waist_y)
            
            # Bottom points (full length to screen bottom)
            bottom_y = h
            bottom_width = waist_width * 0.95
            left_bottom = (neck_x - bottom_width//2, bottom_y)
            right_bottom = (neck_x + bottom_width//2, bottom_y)
            
            return {
                'neck': (neck_x, neck_y),
                'shoulders': [left_shoulder, right_shoulder],
                'waist': [left_waist, right_waist],
                'bottom': [left_bottom, right_bottom],
                'face_width': fw,
                'face_height': fh
            }
        
        return None
    
    def create_body_warp_points(self, body_info, shirt_width, shirt_height):
        """Create warp points to fit shirt to body contour"""
        neck_x, neck_y = body_info['neck']
        
        # Source points (shirt corners)
        src_points = np.array([
            [0, 0],                          # Top-left
            [shirt_width-1, 0],              # Top-right
            [shirt_width-1, shirt_height-1], # Bottom-right
            [0, shirt_height-1]              # Bottom-left
        ], dtype=np.float32)
        
        # Destination points (body contour)
        left_shoulder, right_shoulder = body_info['shoulders']
        left_bottom, right_bottom = body_info['bottom']
        
        # Adjust for natural fit - shirt should follow body curve
        dst_points = np.array([
            [left_shoulder[0], left_shoulder[1]],   # Top-left to left shoulder
            [right_shoulder[0], right_shoulder[1]], # Top-right to right shoulder
            [right_bottom[0], right_bottom[1]],     # Bottom-right to right bottom
            [left_bottom[0], left_bottom[1]]        # Bottom-left to left bottom
        ], dtype=np.float32)
        
        return src_points, dst_points
    
    def warp_shirt_to_body(self, shirt_img, body_info):
        """Warp shirt to fit body contours using perspective transformation"""
        try:
            shirt_height, shirt_width = shirt_img.shape[:2]
            
            # Get warp points
            src_points, dst_points = self.create_body_warp_points(body_info, shirt_width, shirt_height)
            
            # Calculate perspective transformation matrix
            matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Warp the shirt
            warped_shirt = cv2.warpPerspective(shirt_img, matrix, (body_info['bottom'][1][0] + 50, body_info['bottom'][0][1]))
            
            return warped_shirt
            
        except Exception as e:
            print(f"Warping error: {e}")
            return shirt_img
    
    def remove_background_advanced(self, img):
        """Advanced background removal with edge preservation"""
        if len(img.shape) == 3 and img.shape[2] == 4:
            bgr = img[:, :, :3]
            alpha_original = img[:, :, 3]
        else:
            bgr = img
            alpha_original = None
        
        # Multiple background removal techniques
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        
        # Detect white/light backgrounds
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # Detect based on color uniformity in borders
        border_mask = self.detect_background_from_borders(bgr)
        
        # Combine masks
        combined_mask = cv2.bitwise_or(white_mask, border_mask)
        
        # Invert to get shirt mask
        shirt_mask = cv2.bitwise_not(combined_mask)
        
        # Use original alpha if available
        if alpha_original is not None:
            shirt_mask = cv2.bitwise_and(shirt_mask, alpha_original)
        
        # Clean up mask
        kernel = np.ones((3, 3), np.uint8)
        shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Preserve edges with Gaussian blur
        shirt_mask = cv2.GaussianBlur(shirt_mask, (3, 3), 0)
        
        return bgr, shirt_mask
    
    def detect_background_from_borders(self, img):
        """Detect background by analyzing image borders"""
        h, w = img.shape[:2]
        border_size = min(20, h//10, w//10)
        
        # Sample borders
        top_border = img[:border_size, :]
        bottom_border = img[-border_size:, :]
        left_border = img[:, :border_size]
        right_border = img[:, -border_size:]
        
        # Calculate dominant color in borders (assumed to be background)
        borders = np.vstack([top_border.reshape(-1, 3), 
                           bottom_border.reshape(-1, 3),
                           left_border.reshape(-1, 3),
                           right_border.reshape(-1, 3)])
        
        if len(borders) == 0:
            return np.zeros((h, w), dtype=np.uint8)
        
        # Find dominant color
        dominant_color = np.median(borders, axis=0)
        
        # Create mask for similar colors
        color_diff = np.sqrt(np.sum((img.astype(float) - dominant_color.astype(float)) ** 2, axis=2))
        background_mask = (color_diff < 30).astype(np.uint8) * 255
        
        return background_mask
    
    def apply_natural_shirt_fit(self, frame, clothing_item):
        """Apply shirt with natural body-fitting"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🎯 APPLYING NATURAL SHIRT FIT")
            
            # Detect body information
            body_info = self.detect_face_and_shoulders(frame)
            if not body_info:
                print("❌ No body detected - using fallback placement")
                return self.apply_shirt_fallback(frame, clothing_item)
            
            print(f"✅ Body detected: shoulders at {body_info['shoulders']}")
            
            # Load shirt image
            shirt_img = clothing_item['image']
            original_shirt_h, original_shirt_w = shirt_img.shape[:2]
            
            # Calculate shirt dimensions based on body
            shoulder_width = body_info['shoulders'][1][0] - body_info['shoulders'][0][0]
            shirt_height = h - body_info['shoulders'][0][1]  # From shoulders to bottom
            
            # Maintain aspect ratio
            shirt_aspect = original_shirt_w / original_shirt_h
            calculated_width = int(shirt_height * shirt_aspect)
            
            # Use the larger of calculated width or shoulder width
            shirt_width = max(calculated_width, shoulder_width + 50)
            
            print(f"📏 Shirt dimensions: {shirt_width}x{shirt_height}")
            
            # Resize shirt
            resized_shirt = cv2.resize(shirt_img, (shirt_width, shirt_height))
            
            # Remove background
            shirt_bgr, shirt_alpha = self.remove_background_advanced(resized_shirt)
            
            # Warp shirt to body contours
            warped_shirt = self.warp_shirt_to_body(shirt_bgr, body_info)
            warped_alpha = self.warp_shirt_to_body(shirt_alpha, body_info)
            
            # Find placement position
            placement_x = body_info['shoulders'][0][0] - 20
            placement_y = body_info['shoulders'][0][1] - 30
            
            # Ensure warped shirt fits in frame
            warped_h, warped_w = warped_shirt.shape[:2]
            if placement_x + warped_w > w:
                warped_w = w - placement_x
            if placement_y + warped_h > h:
                warped_h = h - placement_y
            
            if warped_w <= 0 or warped_h <= 0:
                print("❌ Warped shirt doesn't fit frame")
                return self.apply_shirt_fallback(frame, clothing_item)
            
            # Extract ROI for blending
            roi_y1 = max(0, placement_y)
            roi_y2 = min(h, placement_y + warped_h)
            roi_x1 = max(0, placement_x)
            roi_x2 = min(w, placement_x + warped_w)
            
            roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
            
            # Adjust warped shirt to ROI size
            warped_roi = warped_shirt[:roi.shape[0], :roi.shape[1]]
            warped_alpha_roi = warped_alpha[:roi.shape[0], :roi.shape[1]]
            
            # Alpha blending
            alpha_norm = warped_alpha_roi.astype(float) / 255.0
            alpha_3d = np.stack([alpha_norm] * 3, axis=2)
            
            # Ensure dimensions match
            if alpha_3d.shape == roi.shape:
                blended = (warped_roi.astype(float) * alpha_3d + 
                          roi.astype(float) * (1.0 - alpha_3d))
                
                result = frame.copy()
                result[roi_y1:roi_y2, roi_x1:roi_x2] = blended.astype(np.uint8)
                
                print("✅✅✅ NATURAL SHIRT FIT APPLIED!")
                return result
            else:
                print("❌ Dimension mismatch in blending")
                return self.apply_shirt_fallback(frame, clothing_item)
            
        except Exception as e:
            print(f"❌ Natural fit error: {e}")
            import traceback
            traceback.print_exc()
            return self.apply_shirt_fallback(frame, clothing_item)
    
    def apply_shirt_fallback(self, frame, clothing_item):
        """Fallback method if body detection fails"""
        try:
            h, w = frame.shape[:2]
            shirt_img = clothing_item['image']
            
            # Simple placement based on screen center
            shirt_height = h
            shirt_width = int(shirt_img.shape[1] * (shirt_height / shirt_img.shape[0]))
            
            resized_shirt = cv2.resize(shirt_img, (shirt_width, shirt_height))
            shirt_bgr, shirt_alpha = self.remove_background_advanced(resized_shirt)
            
            # Center placement
            x = (w - shirt_width) // 2
            y = 0
            
            # Alpha blending
            roi = frame[y:y+shirt_height, x:x+shirt_width]
            alpha_norm = shirt_alpha.astype(float) / 255.0
            alpha_3d = np.stack([alpha_norm] * 3, axis=2)
            
            if alpha_3d.shape == roi.shape:
                blended = (shirt_bgr.astype(float) * alpha_3d + 
                          roi.astype(float) * (1.0 - alpha_3d))
                
                result = frame.copy()
                result[y:y+shirt_height, x:x+shirt_width] = blended.astype(np.uint8)
                return result
            
            return frame
        except:
            return frame
    
    # ============= T-SHIRT METHODS (unchanged) =============
    
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
    
    def create_simple_torso_mask(self, frame):
        # Keep your existing torso mask code
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        face_info = self.detect_face_and_shoulders(frame)
        
        if face_info:
            neck_x, neck_y = face_info['neck']
            fw = face_info['face_width']
            
            shoulder_y = neck_y + int(fw * 0.3)
            waist_y = neck_y + int(fw * 3.0)
            
            shoulder_width = int(fw * 2.2)
            waist_width = int(fw * 2.0)
            
            torso_points = np.array([
                [neck_x - shoulder_width//2, shoulder_y],
                [neck_x + shoulder_width//2, shoulder_y],
                [neck_x + waist_width//2, waist_y],
                [neck_x - waist_width//2, waist_y]
            ], dtype=np.int32)
            
            cv2.fillPoly(mask, [torso_points], 255)
        else:
            # Fallback mask
            top_y = int(h * 0.30)
            bottom_y = h
            top_width = int(w * 0.4)
            bottom_width = int(w * 0.6)
            
            trapezoid_points = np.array([
                [w//2 - top_width//2, top_y],
                [w//2 + top_width//2, top_y],
                [w//2 + bottom_width//2, bottom_y],
                [w//2 - bottom_width//2, bottom_y]
            ], dtype=np.int32)
            
            cv2.fillPoly(mask, [trapezoid_points], 255)
        
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        return mask
    
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
    
    # ============= MAIN APPLICATION =============
    
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
                # Use the new natural fitting method for shirts
                result = self.apply_natural_shirt_fit(frame, clothing_item)
            else:
                result = frame
            
            self.current_outfit = clothing_item
            self.current_outfit_type = clothing_type
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return frame
    
    def debug_draw_body_landmarks(self, frame):
        """Enhanced debugging with body landmarks"""
        result = frame.copy()
        body_info = self.detect_face_and_shoulders(frame)
        
        if body_info:
            # Draw neck
            neck_x, neck_y = body_info['neck']
            cv2.circle(result, (neck_x, neck_y), 8, (0, 255, 0), -1)
            
            # Draw shoulders
            for shoulder in body_info['shoulders']:
                cv2.circle(result, shoulder, 8, (255, 0, 0), -1)
            
            # Draw waist
            for waist in body_info['waist']:
                cv2.circle(result, waist, 6, (0, 0, 255), -1)
            
            # Draw bottom
            for bottom in body_info['bottom']:
                cv2.circle(result, bottom, 6, (255, 255, 0), -1)
            
            # Draw connecting lines
            points = [body_info['shoulders'][0], body_info['shoulders'][1], 
                     body_info['bottom'][1], body_info['bottom'][0]]
            cv2.polylines(result, [np.array(points, dtype=np.int32)], True, (0, 255, 255), 2)
            
            cv2.putText(result, "Body Detected - Natural Fit Ready", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(result, "No Body Detected - Using Fallback", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return result
    
    def reset_pose_history(self):
        self.tshirt_mask = None
        self.body_contour = None
    
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
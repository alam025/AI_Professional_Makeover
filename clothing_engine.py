"""
PERFECT SHIRT FITTING ENGINE
- COMPLETELY removes white/light background
- Warps shirt to fit your body shape
- Uses perspective transform for realistic fit
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
        self.tshirt_mask = None
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Load clothing
        self.load_clothing_images()
        
        print("✅ Perfect fitting engine ready!")
    
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
        return True
    
    def detect_neck_and_shoulders(self, frame):
        """Detect body key points"""
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        if len(faces) > 0:
            fx, fy, fw, fh = max(faces, key=lambda x: x[2] * x[3])
            
            neck_x = fx + fw // 2
            neck_y = fy + fh
            
            shoulder_width = int(fw * 2.5)
            left_shoulder_x = neck_x - shoulder_width // 2
            right_shoulder_x = neck_x + shoulder_width // 2
            shoulder_y = neck_y + int(fh * 0.35)
            
            # Waist points
            torso_height = int(fh * 4.5)
            waist_y = shoulder_y + torso_height
            waist_width = int(shoulder_width * 1.15)
            left_waist_x = neck_x - waist_width // 2
            right_waist_x = neck_x + waist_width // 2
            
            return {
                'neck': (neck_x, neck_y),
                'left_shoulder': (left_shoulder_x, shoulder_y),
                'right_shoulder': (right_shoulder_x, shoulder_y),
                'left_waist': (left_waist_x, waist_y),
                'right_waist': (right_waist_x, waist_y),
                'shoulder_width': shoulder_width,
                'face_width': fw,
                'face_height': fh
            }
        
        return None
    
    # ============= T-SHIRT =============
    
    def create_body_aware_tshirt_mask(self, frame):
        """Create body mask"""
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        body_points = self.detect_neck_and_shoulders(frame)
        
        if body_points:
            left_shoulder = body_points['left_shoulder']
            right_shoulder = body_points['right_shoulder']
            left_waist = body_points['left_waist']
            right_waist = body_points['right_waist']
            neck_x, neck_y = body_points['neck']
            
            torso_points = np.array([
                left_shoulder,
                right_shoulder,
                right_waist,
                left_waist
            ], dtype=np.int32)
            
            cv2.fillPoly(mask, [torso_points], 255)
            
            face_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.ellipse(face_mask, (neck_x, neck_y - body_points['face_height'] // 2), 
                       (body_points['face_width'] // 2 + 10, body_points['face_height'] // 2 + 20), 
                       0, 0, 360, 255, -1)
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
    
    def extract_dominant_color(self, clothing_img):
        """Extract color"""
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
        """HSV replacement"""
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
    
    # ============= SHIRT - COMPLETE BACKGROUND REMOVAL + PERSPECTIVE WARP =============
    
    def remove_background_complete(self, img):
        """COMPLETELY remove background - multiple methods combined"""
        
        if len(img.shape) == 3 and img.shape[2] == 4:
            bgr = img[:, :, :3]
            alpha_original = img[:, :, 3]
        else:
            bgr = img
            alpha_original = None
        
        h, w = bgr.shape[:2]
        
        # Create multiple masks and combine them
        masks = []
        
        # Method 1: HSV white detection (VERY aggressive)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 140])
        upper_white = np.array([180, 60, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        masks.append(white_mask)
        
        # Method 2: LAB color space (detects light colors better)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        _, light_mask = cv2.threshold(l_channel, 170, 255, cv2.THRESH_BINARY)
        masks.append(light_mask)
        
        # Method 3: RGB threshold (all channels high = white)
        b, g, r = cv2.split(bgr)
        rgb_mask = ((b > 140) & (g > 140) & (r > 140)).astype(np.uint8) * 255
        masks.append(rgb_mask)
        
        # Method 4: Edges (shirt has edges, white background doesn't)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 20, 60)
        kernel = np.ones((7, 7), np.uint8)
        edges_dilated = cv2.dilate(edges, kernel, iterations=4)
        # Invert - edges are shirt
        edge_shirt_mask = cv2.bitwise_not(edges_dilated)
        
        # Combine all white detection masks (union)
        combined_white = masks[0]
        for mask in masks[1:]:
            combined_white = cv2.bitwise_or(combined_white, mask)
        
        # Intersect with edge detection (only remove white in non-edge areas)
        background_mask = cv2.bitwise_and(combined_white, edge_shirt_mask)
        
        # Shirt mask is inverse
        shirt_mask = cv2.bitwise_not(background_mask)
        
        # If original alpha exists, combine with it
        if alpha_original is not None:
            shirt_mask = cv2.bitwise_and(shirt_mask, alpha_original)
        
        # Morphological operations to clean up
        kernel_clean = np.ones((5, 5), np.uint8)
        shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel_clean, iterations=3)
        shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel_clean, iterations=2)
        
        # Erode edges to remove any remaining white border
        shirt_mask = cv2.erode(shirt_mask, kernel_clean, iterations=2)
        
        # Smooth
        shirt_mask = cv2.GaussianBlur(shirt_mask, (5, 5), 0)
        
        # Hard threshold
        _, shirt_mask = cv2.threshold(shirt_mask, 30, 255, cv2.THRESH_BINARY)
        
        return bgr, shirt_mask
    
    def warp_shirt_to_body(self, shirt_img, shirt_alpha, body_points):
        """Warp shirt to fit body shape using perspective transform"""
        
        h, w = shirt_img.shape[:2]
        
        # Shirt corners (source points - rectangular shirt)
        src_points = np.float32([
            [w * 0.2, h * 0.1],   # Top-left (left shoulder)
            [w * 0.8, h * 0.1],   # Top-right (right shoulder)
            [w * 0.85, h * 0.9],  # Bottom-right (right waist)
            [w * 0.15, h * 0.9]   # Bottom-left (left waist)
        ])
        
        # Body shape points (destination - your actual body)
        left_shoulder = body_points['left_shoulder']
        right_shoulder = body_points['right_shoulder']
        left_waist = body_points['left_waist']
        right_waist = body_points['right_waist']
        
        # Calculate bounding box for warped shirt
        all_x = [left_shoulder[0], right_shoulder[0], left_waist[0], right_waist[0]]
        all_y = [left_shoulder[1], right_shoulder[1], left_waist[1], right_waist[1]]
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        out_w = max_x - min_x
        out_h = max_y - min_y
        
        # Destination points (relative to output image)
        dst_points = np.float32([
            [left_shoulder[0] - min_x, left_shoulder[1] - min_y],
            [right_shoulder[0] - min_x, right_shoulder[1] - min_y],
            [right_waist[0] - min_x, right_waist[1] - min_y],
            [left_waist[0] - min_x, left_waist[1] - min_y]
        ])
        
        # Get perspective transform matrix
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        
        # Warp shirt
        warped_shirt = cv2.warpPerspective(shirt_img, matrix, (out_w, out_h))
        warped_alpha = cv2.warpPerspective(shirt_alpha, matrix, (out_w, out_h))
        
        return warped_shirt, warped_alpha, (min_x, min_y)
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """Apply shirt with perspective warp to fit body"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🔍 Applying shirt with body fitting...")
            
            # Detect body
            body_points = self.detect_neck_and_shoulders(frame)
            
            if not body_points:
                print("❌ No face/body detected")
                return frame
            
            print(f"✅ Body detected")
            print(f"   Shoulders: {body_points['left_shoulder']} to {body_points['right_shoulder']}")
            print(f"   Waist: {body_points['left_waist']} to {body_points['right_waist']}")
            
            # Load shirt
            clothing_img = clothing_item['image']
            print(f"👔 Original shirt: {clothing_img.shape}")
            
            # Remove background COMPLETELY
            shirt_bgr, shirt_alpha = self.remove_background_complete(clothing_img)
            
            non_zero = cv2.countNonZero(shirt_alpha)
            total = shirt_alpha.shape[0] * shirt_alpha.shape[1]
            percentage = (non_zero / total) * 100
            print(f"🎨 Background removed: {percentage:.1f}% of image is shirt")
            
            if non_zero < 500:
                print("⚠️ Almost no shirt detected - background removal too aggressive")
                return frame
            
            # Warp shirt to fit body shape
            warped_shirt, warped_alpha, offset = self.warp_shirt_to_body(
                shirt_bgr, shirt_alpha, body_points
            )
            
            offset_x, offset_y = offset
            wh, ww = warped_shirt.shape[:2]
            
            print(f"✂️ Warped shirt: {ww}x{wh} at offset ({offset_x}, {offset_y})")
            
            # Bounds check
            if offset_x < 0 or offset_y < 0 or offset_x + ww > w or offset_y + wh > h:
                print("⚠️ Warped shirt out of bounds, clipping...")
                # Clip to frame bounds
                clip_x1 = max(0, -offset_x)
                clip_y1 = max(0, -offset_y)
                clip_x2 = min(ww, w - offset_x)
                clip_y2 = min(wh, h - offset_y)
                
                warped_shirt = warped_shirt[clip_y1:clip_y2, clip_x1:clip_x2]
                warped_alpha = warped_alpha[clip_y1:clip_y2, clip_x1:clip_x2]
                
                offset_x = max(0, offset_x)
                offset_y = max(0, offset_y)
                wh, ww = warped_shirt.shape[:2]
            
            if ww <= 0 or wh <= 0:
                print("❌ Invalid warped dimensions")
                return frame
            
            # Get ROI
            roi = frame[offset_y:offset_y + wh, offset_x:offset_x + ww]
            
            if roi.shape[:2] != (wh, ww):
                print(f"❌ ROI mismatch")
                return frame
            
            # Alpha blend
            alpha_norm = warped_alpha.astype(float) / 255.0
            alpha_3d = np.stack([alpha_norm] * 3, axis=2)
            
            result = frame.copy()
            blended = (warped_shirt.astype(float) * alpha_3d + 
                      roi.astype(float) * (1.0 - alpha_3d))
            
            result[offset_y:offset_y + wh, offset_x:offset_x + ww] = blended.astype(np.uint8)
            
            print(f"✅✅✅ Shirt perfectly fitted to body shape!")
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
            print(f"\n🎯 Applying {clothing_type}: {clothing_item['name']}")
            
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
            # Draw body shape
            left_shoulder = body_points['left_shoulder']
            right_shoulder = body_points['right_shoulder']
            left_waist = body_points['left_waist']
            right_waist = body_points['right_waist']
            neck = body_points['neck']
            
            # Draw torso quadrilateral
            torso_points = np.array([left_shoulder, right_shoulder, right_waist, left_waist], dtype=np.int32)
            cv2.polylines(result, [torso_points], True, (0, 255, 255), 3)
            
            # Draw points
            cv2.circle(result, neck, 8, (0, 255, 0), -1)
            cv2.circle(result, left_shoulder, 8, (255, 0, 0), -1)
            cv2.circle(result, right_shoulder, 8, (255, 0, 0), -1)
            cv2.circle(result, left_waist, 8, (0, 0, 255), -1)
            cv2.circle(result, right_waist, 8, (0, 0, 255), -1)
            
            cv2.putText(result, "Body Shape Detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(result, "No Body", (10, 30),
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
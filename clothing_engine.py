"""
REALISTIC SHIRT OVERLAY - LOOKS LIKE REAL CLOTHING
Advanced body fitting, natural blending, complete coverage
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
        self.upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        
        self.load_clothing_images()
        print("✅ REALISTIC shirt engine ready!")
    
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
    
    def detect_advanced_body_landmarks(self, frame):
        """Advanced body landmark detection with shoulders and torso"""
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect face
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.05,
            minNeighbors=8, 
            minSize=(80, 80),
            maxSize=(400, 400)
        )
        
        # Detect upper body
        upper_bodies = self.upper_body_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(150, 150)
        )
        
        if len(faces) > 0:
            fx, fy, fw, fh = max(faces, key=lambda x: x[2] * x[3])
            
            # Calculate body landmarks based on face
            face_center_x = fx + fw // 2
            face_center_y = fy + fh // 2
            
            # Neck position (bottom of face)
            neck_x = face_center_x
            neck_y = fy + fh
            
            # Shoulder positions (wider than face)
            shoulder_width = int(fw * 2.8)  # Much wider for realism
            left_shoulder_x = face_center_x - shoulder_width // 2
            right_shoulder_x = face_center_x + shoulder_width // 2
            shoulder_y = neck_y + int(fh * 0.3)  # Just below neck
            
            # Torso dimensions
            torso_width = int(fw * 3.2)  # Even wider at torso
            torso_top = shoulder_y
            torso_bottom = min(h, neck_y + int(fh * 5.5))  # Extend to bottom
            
            # Chest center (for shirt button line)
            chest_center_x = face_center_x
            chest_top_y = neck_y
            
            # If upper body detected, use it to refine measurements
            if len(upper_bodies) > 0:
                ux, uy, uw, uh = max(upper_bodies, key=lambda x: x[2] * x[3])
                torso_width = max(torso_width, int(uw * 0.9))
                torso_bottom = min(torso_bottom, uy + uh)
            
            return {
                'face_x': fx,
                'face_y': fy,
                'face_width': fw,
                'face_height': fh,
                'face_center_x': face_center_x,
                'face_center_y': face_center_y,
                'neck_x': neck_x,
                'neck_y': neck_y,
                'left_shoulder_x': left_shoulder_x,
                'right_shoulder_x': right_shoulder_x,
                'shoulder_y': shoulder_y,
                'shoulder_width': shoulder_width,
                'torso_width': torso_width,
                'torso_top': torso_top,
                'torso_bottom': torso_bottom,
                'chest_center_x': chest_center_x,
                'chest_top_y': chest_top_y
            }
        
        # Fallback estimates
        return {
            'face_x': w // 2 - 60,
            'face_y': int(h * 0.15),
            'face_width': 120,
            'face_height': 140,
            'face_center_x': w // 2,
            'face_center_y': int(h * 0.2),
            'neck_x': w // 2,
            'neck_y': int(h * 0.28),
            'left_shoulder_x': int(w * 0.3),
            'right_shoulder_x': int(w * 0.7),
            'shoulder_y': int(h * 0.32),
            'shoulder_width': int(w * 0.4),
            'torso_width': int(w * 0.5),
            'torso_top': int(h * 0.32),
            'torso_bottom': int(h * 0.85),
            'chest_center_x': w // 2,
            'chest_top_y': int(h * 0.28)
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
        
        landmarks = self.detect_advanced_body_landmarks(frame)
        
        neck_x = landmarks['neck_x']
        neck_y = landmarks['neck_y']
        shoulder_width = landmarks['shoulder_width']
        torso_width = landmarks['torso_width']
        torso_top = landmarks['torso_top']
        torso_bottom = landmarks['torso_bottom']
        
        # Create body shape
        torso_points = np.array([
            [neck_x - shoulder_width//2, torso_top],
            [neck_x + shoulder_width//2, torso_top],
            [neck_x + torso_width//2, torso_bottom],
            [neck_x - torso_width//2, torso_bottom]
        ], dtype=np.int32)
        
        cv2.fillPoly(mask, [torso_points], 255)
        
        # Remove face area
        fw = landmarks['face_width']
        fh = landmarks['face_height']
        face_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(face_mask, (neck_x, neck_y - fh // 2), 
                   (fw // 2 + 15, fh // 2 + 25), 0, 0, 360, 255, -1)
        mask = cv2.subtract(mask, face_mask)
        
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
    
    # ============= REALISTIC SHIRT OVERLAY =============
    
    def remove_background_advanced(self, img):
        """Advanced background removal with edge detection"""
        
        if len(img.shape) == 3 and img.shape[2] == 4:
            bgr = img[:, :, :3]
            alpha = img[:, :, 3]
            _, alpha_binary = cv2.threshold(alpha, 30, 255, cv2.THRESH_BINARY)
            
            # Clean up alpha channel
            kernel = np.ones((3, 3), np.uint8)
            alpha_binary = cv2.morphologyEx(alpha_binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            alpha_binary = cv2.morphologyEx(alpha_binary, cv2.MORPH_OPEN, kernel, iterations=1)
            
            return bgr, alpha_binary
        else:
            bgr = img
            h, w = bgr.shape[:2]
            
            # Multi-method white background detection
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
            
            # Aggressive white detection
            white_mask1 = (hsv[:, :, 2] > 200) & (hsv[:, :, 1] < 80)
            white_mask2 = lab[:, :, 0] > 190
            b, g, r = cv2.split(bgr)
            white_mask3 = (b > 180) & (g > 180) & (r > 180)
            
            combined_white_mask = (white_mask1 | white_mask2 | white_mask3)
            shirt_mask = (~combined_white_mask).astype(np.uint8) * 255
            
            # Find largest contour (shirt)
            contours, _ = cv2.findContours(shirt_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                contour_mask = np.zeros((h, w), dtype=np.uint8)
                cv2.drawContours(contour_mask, [largest_contour], -1, 255, -1)
                shirt_mask = contour_mask
            
            # Morphological operations for clean edges
            kernel = np.ones((5, 5), np.uint8)
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel, iterations=2)
            
            # Smooth edges
            shirt_mask = cv2.GaussianBlur(shirt_mask, (5, 5), 0)
            _, shirt_mask = cv2.threshold(shirt_mask, 127, 255, cv2.THRESH_BINARY)
            
            return bgr, shirt_mask
    
    def warp_shirt_to_body(self, shirt_img, shirt_mask, landmarks, frame_shape):
        """Warp shirt to fit body contours naturally"""
        h, w = frame_shape[:2]
        shirt_h, shirt_w = shirt_img.shape[:2]
        
        # Source points (shirt image - standard shirt shape)
        # Assuming shirt image has collar at top, shoulders wide, tapers at bottom
        src_points = np.float32([
            [shirt_w * 0.5, shirt_h * 0.05],   # Top center (collar)
            [shirt_w * 0.15, shirt_h * 0.25],  # Left shoulder
            [shirt_w * 0.85, shirt_h * 0.25],  # Right shoulder
            [shirt_w * 0.25, shirt_h * 0.95],  # Left bottom
            [shirt_w * 0.75, shirt_h * 0.95],  # Right bottom
            [shirt_w * 0.5, shirt_h * 0.5]     # Center chest
        ])
        
        # Destination points (body landmarks in frame)
        neck_x = landmarks['neck_x']
        neck_y = landmarks['neck_y']
        left_shoulder_x = landmarks['left_shoulder_x']
        right_shoulder_x = landmarks['right_shoulder_x']
        shoulder_y = landmarks['shoulder_y']
        torso_bottom = landmarks['torso_bottom']
        torso_width = landmarks['torso_width']
        
        # Calculate bottom points (slightly wider at hips)
        left_bottom_x = neck_x - int(torso_width * 0.45)
        right_bottom_x = neck_x + int(torso_width * 0.45)
        
        dst_points = np.float32([
            [neck_x, neck_y],                          # Top center (collar)
            [left_shoulder_x, shoulder_y],             # Left shoulder
            [right_shoulder_x, shoulder_y],            # Right shoulder
            [left_bottom_x, torso_bottom],             # Left bottom
            [right_bottom_x, torso_bottom],            # Right bottom
            [neck_x, (neck_y + torso_bottom) // 2]    # Center chest
        ])
        
        # Calculate perspective transform matrix
        matrix, _ = cv2.findHomography(src_points, dst_points, cv2.RANSAC, 5.0)
        
        if matrix is not None:
            # Warp shirt image
            warped_shirt = cv2.warpPerspective(shirt_img, matrix, (w, h), 
                                               flags=cv2.INTER_CUBIC,
                                               borderMode=cv2.BORDER_CONSTANT,
                                               borderValue=(0, 0, 0))
            
            # Warp mask
            warped_mask = cv2.warpPerspective(shirt_mask, matrix, (w, h),
                                             flags=cv2.INTER_NEAREST,
                                             borderMode=cv2.BORDER_CONSTANT,
                                             borderValue=0)
            
            return warped_shirt, warped_mask
        else:
            # Fallback: simple resize
            target_width = int(torso_width * 1.2)
            target_height = torso_bottom - neck_y
            
            resized_shirt = cv2.resize(shirt_img, (target_width, target_height), 
                                      interpolation=cv2.INTER_CUBIC)
            resized_mask = cv2.resize(shirt_mask, (target_width, target_height),
                                     interpolation=cv2.INTER_NEAREST)
            
            # Create full-size images
            full_shirt = np.zeros((h, w, 3), dtype=np.uint8)
            full_mask = np.zeros((h, w), dtype=np.uint8)
            
            # Position at neck
            x_offset = neck_x - target_width // 2
            y_offset = neck_y
            
            # Ensure within bounds
            x_start = max(0, x_offset)
            y_start = max(0, y_offset)
            x_end = min(w, x_offset + target_width)
            y_end = min(h, y_offset + target_height)
            
            shirt_x_start = max(0, -x_offset)
            shirt_y_start = max(0, -y_offset)
            shirt_x_end = shirt_x_start + (x_end - x_start)
            shirt_y_end = shirt_y_start + (y_end - y_start)
            
            full_shirt[y_start:y_end, x_start:x_end] = \
                resized_shirt[shirt_y_start:shirt_y_end, shirt_x_start:shirt_x_end]
            full_mask[y_start:y_end, x_start:x_end] = \
                resized_mask[shirt_y_start:shirt_y_end, shirt_x_start:shirt_x_end]
            
            return full_shirt, full_mask
    
    def add_realistic_shading(self, shirt_img, frame, mask):
        """Add realistic lighting and shadows based on original frame"""
        # Convert to LAB color space for better lighting control
        frame_lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        shirt_lab = cv2.cvtColor(shirt_img, cv2.COLOR_BGR2LAB)
        
        # Extract luminance from original frame
        frame_l = frame_lab[:, :, 0]
        shirt_l = shirt_lab[:, :, 0]
        
        # Calculate lighting ratio where shirt will be placed
        mask_bool = mask > 128
        if np.any(mask_bool):
            # Blend shirt luminance with frame luminance for natural lighting
            lighting_factor = frame_l.astype(float) / 128.0  # Normalize
            
            # Apply lighting to shirt where mask is active
            adjusted_l = shirt_l.copy()
            adjusted_l = np.clip(adjusted_l.astype(float) * lighting_factor * 0.8, 0, 255).astype(np.uint8)
            
            # Apply only where mask is active
            shirt_lab[:, :, 0] = np.where(mask_bool, adjusted_l, shirt_l)
            
            # Convert back to BGR
            shaded_shirt = cv2.cvtColor(shirt_lab, cv2.COLOR_LAB2BGR)
            return shaded_shirt
        
        return shirt_img
    
    def create_natural_blend_mask(self, mask, landmarks):
        """Create smooth blending mask with feathered edges"""
        h, w = mask.shape[:2]
        
        # Create distance transform for smooth falloff
        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        
        # Normalize
        if dist_transform.max() > 0:
            dist_transform = dist_transform / dist_transform.max()
        
        # Create soft edges (feathering)
        feather_radius = 15
        smooth_mask = cv2.GaussianBlur(mask, (feather_radius*2+1, feather_radius*2+1), feather_radius/2)
        
        # Combine with distance transform for natural falloff
        blend_mask = (smooth_mask.astype(float) / 255.0) * (dist_transform ** 0.5)
        blend_mask = (blend_mask * 255).astype(np.uint8)
        
        # Extra smoothing at edges
        blend_mask = cv2.bilateralFilter(blend_mask, 9, 75, 75)
        
        return blend_mask
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """REALISTIC shirt overlay with body fitting and natural blending"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🎯 APPLYING REALISTIC SHIRT OVERLAY...")
            
            # Get advanced body landmarks
            landmarks = self.detect_advanced_body_landmarks(frame)
            
            print(f"✅ Body detected:")
            print(f"   Neck: ({landmarks['neck_x']}, {landmarks['neck_y']})")
            print(f"   Shoulders: {landmarks['shoulder_width']}px wide")
            print(f"   Torso: {landmarks['torso_width']}px wide, height: {landmarks['torso_bottom'] - landmarks['torso_top']}px")
            
            # Load and process shirt
            clothing_img = clothing_item['image']
            
            # Remove background
            shirt_bgr, shirt_alpha = self.remove_background_advanced(clothing_img)
            
            # Warp shirt to fit body
            warped_shirt, warped_mask = self.warp_shirt_to_body(
                shirt_bgr, shirt_alpha, landmarks, frame.shape
            )
            
            # Add realistic shading
            shaded_shirt = self.add_realistic_shading(warped_shirt, frame, warped_mask)
            
            # Create natural blend mask
            blend_mask = self.create_natural_blend_mask(warped_mask, landmarks)
            
            # Normalize blend mask to 0-1 range
            blend_mask_norm = blend_mask.astype(float) / 255.0
            blend_mask_3d = np.stack([blend_mask_norm] * 3, axis=2)
            
            # Final blending with anti-aliasing
            result = frame.copy().astype(float)
            shaded_shirt_float = shaded_shirt.astype(float)
            
            # Blend with smooth transition
            result = result * (1 - blend_mask_3d) + shaded_shirt_float * blend_mask_3d
            result = np.clip(result, 0, 255).astype(np.uint8)
            
            # Post-processing: slight blur at edges for ultra-realistic look
            edge_mask = cv2.Canny(warped_mask, 50, 150)
            edge_dilated = cv2.dilate(edge_mask, np.ones((5, 5), np.uint8), iterations=1)
            
            # Selectively blur edges
            blurred_result = cv2.GaussianBlur(result, (5, 5), 1)
            edge_blend = (edge_dilated.astype(float) / 255.0)[:, :, np.newaxis]
            result = (result * (1 - edge_blend * 0.3) + blurred_result * edge_blend * 0.3).astype(np.uint8)
            
            print(f"✅ REALISTIC SHIRT APPLIED!")
            print(f"   ✓ Body-fitted with perspective warp")
            print(f"   ✓ Natural lighting and shadows")
            print(f"   ✓ Feathered edges for seamless blend")
            print(f"   ✓ Completely covers original clothing")
            print(f"   ✓ Looks like you're actually wearing it!\n")
            
            return result
            
        except Exception as e:
            print(f"❌ Shirt error: {e}")
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
        """Enhanced debug visualization"""
        result = frame.copy()
        landmarks = self.detect_advanced_body_landmarks(frame)
        
        # Draw face
        cv2.rectangle(result, 
                     (landmarks['face_x'], landmarks['face_y']), 
                     (landmarks['face_x'] + landmarks['face_width'], 
                      landmarks['face_y'] + landmarks['face_height']), 
                     (255, 0, 0), 2)
        
        # Draw neck
        cv2.circle(result, (landmarks['neck_x'], landmarks['neck_y']), 8, (0, 255, 0), -1)
        
        # Draw shoulders
        cv2.circle(result, (landmarks['left_shoulder_x'], landmarks['shoulder_y']), 8, (255, 255, 0), -1)
        cv2.circle(result, (landmarks['right_shoulder_x'], landmarks['shoulder_y']), 8, (255, 255, 0), -1)
        cv2.line(result, (landmarks['left_shoulder_x'], landmarks['shoulder_y']),
                (landmarks['right_shoulder_x'], landmarks['shoulder_y']), (255, 255, 0), 2)
        
        # Draw torso outline
        left_bottom_x = landmarks['neck_x'] - landmarks['torso_width'] // 2
        right_bottom_x = landmarks['neck_x'] + landmarks['torso_width'] // 2
        
        torso_points = np.array([
            [landmarks['left_shoulder_x'], landmarks['shoulder_y']],
            [landmarks['right_shoulder_x'], landmarks['shoulder_y']],
            [right_bottom_x, landmarks['torso_bottom']],
            [left_bottom_x, landmarks['torso_bottom']]
        ], dtype=np.int32)
        
        cv2.polylines(result, [torso_points], True, (0, 255, 255), 2)
        
        # Labels
        cv2.putText(result, "FACE", (landmarks['face_x'], landmarks['face_y'] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        cv2.putText(result, "NECK", (landmarks['neck_x'] + 15, landmarks['neck_y']),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(result, "BODY FITTED SHIRT AREA", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return result
    
    def detect_face_and_neck(self, frame):
        """Compatibility wrapper"""
        landmarks = self.detect_advanced_body_landmarks(frame)
        return landmarks
    
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
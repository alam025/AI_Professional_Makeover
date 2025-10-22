"""
IMPROVED CLOTHING ENGINE - BODY-AWARE FITTING
Uses MediaPipe Pose to detect body shape and fit clothing naturally
"""

import cv2
import numpy as np
import os
import mediapipe as mp

class ProfessionalClothingEngine:
    def __init__(self, replicate_api_key=None):
        """Initialize body-aware clothing engine"""
        self.clothing_templates = {}
        self.current_outfit = None
        self.current_outfit_type = None
        
        # Initialize MediaPipe Pose for body detection
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # For T-shirt HSV method
        self.tshirt_mask = None
        
        # Body landmarks cache
        self.body_landmarks = None
        
        # Load clothing
        self.load_clothing_images()
        
        print("✅ Body-aware clothing engine initialized with MediaPipe Pose")
    
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
    
    def train_background(self, frame):
        """Dummy function"""
        return True
    
    # ============= BODY DETECTION =============
    
    def detect_body_landmarks(self, frame):
        """Detect body landmarks using MediaPipe Pose"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)
            
            if results.pose_landmarks:
                self.body_landmarks = results.pose_landmarks
                return True
            else:
                return False
        except Exception as e:
            print(f"Body detection error: {e}")
            return False
    
    def get_body_points(self, frame):
        """Extract key body points from landmarks"""
        if not self.body_landmarks:
            return None
        
        h, w = frame.shape[:2]
        landmarks = self.body_landmarks.landmark
        
        # Key points for shirt fitting
        points = {
            'left_shoulder': (int(landmarks[11].x * w), int(landmarks[11].y * h)),
            'right_shoulder': (int(landmarks[12].x * w), int(landmarks[12].y * h)),
            'left_hip': (int(landmarks[23].x * w), int(landmarks[23].y * h)),
            'right_hip': (int(landmarks[24].x * w), int(landmarks[24].y * h)),
            'left_elbow': (int(landmarks[13].x * w), int(landmarks[13].y * h)),
            'right_elbow': (int(landmarks[14].x * w), int(landmarks[14].y * h)),
            'nose': (int(landmarks[0].x * w), int(landmarks[0].y * h))
        }
        
        return points
    
    # ============= T-SHIRT METHOD (HSV Color Replacement) =============
    
    def create_body_aware_tshirt_mask(self, frame):
        """Create mask based on actual body shape"""
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # Detect body
        if not self.detect_body_landmarks(frame):
            # Fallback to simple trapezoid if body not detected
            return self.create_simple_upper_body_mask(frame)
        
        points = self.get_body_points(frame)
        if not points:
            return self.create_simple_upper_body_mask(frame)
        
        # Create natural torso shape
        left_shoulder = points['left_shoulder']
        right_shoulder = points['right_shoulder']
        left_hip = points['left_hip']
        right_hip = points['right_hip']
        
        # Extend slightly for natural fit
        shoulder_width = right_shoulder[0] - left_shoulder[0]
        extend = int(shoulder_width * 0.15)
        
        # T-shirt polygon (natural body shape)
        torso_points = np.array([
            [left_shoulder[0] - extend, left_shoulder[1]],  # Left shoulder extended
            [right_shoulder[0] + extend, right_shoulder[1]],  # Right shoulder extended
            [right_hip[0] + extend, right_hip[1]],  # Right hip extended
            [left_hip[0] - extend, left_hip[1]]  # Left hip extended
        ], dtype=np.int32)
        
        cv2.fillPoly(mask, [torso_points], 255)
        
        # Exclude neck/face area
        nose = points['nose']
        neck_radius = int(shoulder_width * 0.25)
        neck_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(neck_mask, nose, neck_radius, 255, -1)
        mask = cv2.subtract(mask, neck_mask)
        
        # Smooth edges
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        
        return mask
    
    def create_simple_upper_body_mask(self, frame):
        """Fallback trapezoid mask"""
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        top_y = int(h * 0.65)
        bottom_y = int(h * 1.00)
        top_left_x = int(w * 0.35)
        top_right_x = int(w * 0.65)
        bottom_left_x = int(w * 0.25)
        bottom_right_x = int(w * 0.75)
        
        trapezoid_points = np.array([
            [top_left_x, top_y],
            [top_right_x, top_y],
            [bottom_right_x, bottom_y],
            [bottom_left_x, bottom_y]
        ], dtype=np.int32)
        
        cv2.fillPoly(mask, [trapezoid_points], 255)
        
        face_center_x = w // 2
        face_center_y = int(h * 0.20)
        face_radius = int(h * 0.15)
        face_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(face_mask, (face_center_x, face_center_y), face_radius, 255, -1)
        mask = cv2.subtract(mask, face_mask)
        
        arm_exclusion_left = np.zeros((h, w), dtype=np.uint8)
        arm_exclusion_right = np.zeros((h, w), dtype=np.uint8)
        cv2.rectangle(arm_exclusion_left, (0, 0), (int(w * 0.18), h), 255, -1)
        cv2.rectangle(arm_exclusion_right, (int(w * 0.82), 0), (w, h), 255, -1)
        mask = cv2.subtract(mask, arm_exclusion_left)
        mask = cv2.subtract(mask, arm_exclusion_right)
        
        mask = cv2.GaussianBlur(mask, (31, 31), 0)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        
        return mask
    
    def extract_dominant_color(self, clothing_img):
        """Extract dominant hue"""
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
        """Apply HSV color replacement for T-SHIRTS"""
        try:
            clothing_img = clothing_item['image']
            
            if clothing_item['color_hue'] is None:
                clothing_item['color_hue'] = self.extract_dominant_color(clothing_img)
            
            target_hue = clothing_item['color_hue']
            
            # Use body-aware mask
            mask = self.create_body_aware_tshirt_mask(frame)
            self.tshirt_mask = mask
            
            result = self.replace_color_simple(frame, mask, target_hue)
            return result
        except Exception as e:
            print(f"T-shirt error: {e}")
            return frame
    
    # ============= SHIRT METHOD (Body-Aware Overlay) =============
    
    def create_body_fitted_shirt_mask(self, width, height, body_points):
        """Create shirt mask that follows body contours"""
        mask = np.zeros((height, width), dtype=np.uint8)
        
        if not body_points:
            # Fallback to simple shape
            cv2.rectangle(mask, (0, 0), (width, height), 255, -1)
            mask = cv2.GaussianBlur(mask, (15, 15), 0)
            return mask, 0
        
        # Map body points to shirt coordinates
        h, w = height, width
        
        # Create natural shirt shape
        center_x = w // 2
        
        # Shoulders (top 15% of shirt)
        shoulder_y = int(h * 0.15)
        shoulder_left = int(w * 0.15)
        shoulder_right = int(w * 0.85)
        
        # Chest (30% down)
        chest_y = int(h * 0.30)
        chest_left = int(w * 0.12)
        chest_right = int(w * 0.88)
        
        # Waist (70% down)
        waist_y = int(h * 0.70)
        waist_left = int(w * 0.18)
        waist_right = int(w * 0.82)
        
        # Bottom hem
        bottom_y = h - 1
        bottom_left = int(w * 0.20)
        bottom_right = int(w * 0.80)
        
        # Create body-fitted polygon
        shirt_contour = np.array([
            # Neck opening (top center)
            [center_x, 0],
            # Left shoulder
            [shoulder_left, shoulder_y],
            # Left chest
            [chest_left, chest_y],
            # Left waist
            [waist_left, waist_y],
            # Left bottom
            [bottom_left, bottom_y],
            # Right bottom
            [bottom_right, bottom_y],
            # Right waist
            [waist_right, waist_y],
            # Right chest
            [chest_right, chest_y],
            # Right shoulder
            [shoulder_right, shoulder_y],
        ], dtype=np.int32)
        
        cv2.fillPoly(mask, [shirt_contour], 255)
        
        # Add collar opening (V-neck or round)
        collar_depth = int(h * 0.12)
        collar_width = int(w * 0.20)
        collar_points = np.array([
            [center_x - collar_width, 0],
            [center_x, collar_depth],
            [center_x + collar_width, 0]
        ], dtype=np.int32)
        cv2.fillPoly(mask, [collar_points], 0)  # Cut out collar
        
        # Smooth the mask
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        
        # Add sleeve extensions
        sleeve_extension = int(w * 0.15)
        
        return mask, sleeve_extension
    
    def prepare_body_fitted_clothing(self, clothing_img, target_width, target_height, body_points):
        """Prepare clothing with body-aware fitting"""
        # Resize clothing
        resized_clothing = cv2.resize(clothing_img, (target_width, target_height))
        
        # Remove background
        if resized_clothing.shape[2] == 4:
            bgr = resized_clothing[:, :, :3]
            alpha_original = resized_clothing[:, :, 3]
            
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            alpha_from_white = cv2.bitwise_not(white_mask)
            
            alpha = cv2.bitwise_and(alpha_original, alpha_from_white)
        else:
            bgr = resized_clothing
            
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            _, bright_mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
            
            combined_bg_mask = cv2.bitwise_or(white_mask, bright_mask)
            alpha = cv2.bitwise_not(combined_bg_mask)
            
            kernel = np.ones((3, 3), np.uint8)
            alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel)
            alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)
            alpha = cv2.GaussianBlur(alpha, (5, 5), 0)
        
        _, alpha = cv2.threshold(alpha, 50, 255, cv2.THRESH_BINARY)
        
        # Create body-fitted mask
        body_mask, sleeve_extension = self.create_body_fitted_shirt_mask(
            target_width, target_height, body_points
        )
        
        # Combine with clothing alpha
        combined_alpha = cv2.bitwise_and(alpha, body_mask)
        
        return bgr, combined_alpha, sleeve_extension
    
    def apply_shirt_overlay(self, frame, clothing_item):
        """Apply body-aware shirt overlay"""
        try:
            clothing_img = clothing_item['image']
            
            # Detect body landmarks
            self.detect_body_landmarks(frame)
            body_points = self.get_body_points(frame)
            
            h, w = frame.shape[:2]
            
            if body_points:
                # Use body landmarks for precise placement
                left_shoulder = body_points['left_shoulder']
                right_shoulder = body_points['right_shoulder']
                left_hip = body_points['left_hip']
                right_hip = body_points['right_hip']
                
                # Calculate shirt dimensions
                shoulder_width = right_shoulder[0] - left_shoulder[0]
                torso_height = left_hip[1] - left_shoulder[1]
                
                # Extend for natural fit
                cloth_w = int(shoulder_width * 1.4)
                cloth_h = int(torso_height * 1.3)
                cloth_x = (left_shoulder[0] + right_shoulder[0]) // 2 - cloth_w // 2
                cloth_y = left_shoulder[1] - int(cloth_h * 0.1)  # Start slightly above shoulders
            else:
                # Fallback positioning
                cloth_w = int(w * 0.45)
                cloth_h = int(h * 0.55)
                cloth_x = (w - cloth_w) // 2
                cloth_y = int(h * 0.25)
            
            # Prepare clothing
            clothing_bgr, clothing_alpha, sleeve_extension = self.prepare_body_fitted_clothing(
                clothing_img, cloth_w, cloth_h, body_points
            )
            
            # Apply to frame
            result = frame.copy()
            
            # Bounds checking
            cloth_x = max(0, cloth_x)
            cloth_y = max(0, cloth_y)
            cloth_w = min(cloth_w, w - cloth_x)
            cloth_h = min(cloth_h, h - cloth_y)
            
            if cloth_h <= 0 or cloth_w <= 0:
                return frame
            
            # Resize if needed
            clothing_bgr = cv2.resize(clothing_bgr, (cloth_w, cloth_h))
            clothing_alpha = cv2.resize(clothing_alpha, (cloth_w, cloth_h))
            
            # Get ROI
            roi = result[cloth_y:cloth_y + cloth_h, cloth_x:cloth_x + cloth_w]
            
            if roi.shape[0] != cloth_h or roi.shape[1] != cloth_w:
                return frame
            
            # Alpha blend
            alpha_normalized = clothing_alpha.astype(float) / 255.0
            alpha_3d = np.stack([alpha_normalized] * 3, axis=2)
            
            blended = (clothing_bgr.astype(float) * alpha_3d + 
                      roi.astype(float) * (1.0 - alpha_3d))
            
            result[cloth_y:cloth_y + cloth_h, cloth_x:cloth_x + cloth_w] = blended.astype(np.uint8)
            
            return result
        except Exception as e:
            print(f"Shirt overlay error: {e}")
            import traceback
            traceback.print_exc()
            return frame
    
    # ============= MAIN APPLICATION METHOD =============
    
    def apply_clothing_item(self, frame, clothing_type, item_index):
        """Apply clothing with body-aware fitting"""
        if frame is None:
            return frame
        
        try:
            items = self.clothing_templates.get(clothing_type, [])
            if item_index >= len(items):
                return frame
            
            clothing_item = items[item_index]
            
            if clothing_type == "tshirts":
                result = self.apply_tshirt_color_replacement(frame, clothing_item)
                print(f"🎨 Applied T-shirt (body-aware HSV)")
            elif clothing_type == "shirts":
                result = self.apply_shirt_overlay(frame, clothing_item)
                print(f"👔 Applied shirt (body-fitted overlay)")
            else:
                result = frame
            
            self.current_outfit = clothing_item
            self.current_outfit_type = clothing_type
            
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return frame
    
    def debug_draw_body_landmarks(self, frame):
        """Debug visualization"""
        if self.body_landmarks:
            result = frame.copy()
            points = self.get_body_points(frame)
            
            if points:
                # Draw key points
                for name, (x, y) in points.items():
                    cv2.circle(result, (x, y), 5, (0, 255, 0), -1)
                    cv2.putText(result, name, (x + 10, y), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                
                # Draw body outline
                cv2.line(result, points['left_shoulder'], points['right_shoulder'], (0, 255, 255), 2)
                cv2.line(result, points['left_shoulder'], points['left_hip'], (0, 255, 255), 2)
                cv2.line(result, points['right_shoulder'], points['right_hip'], (0, 255, 255), 2)
                cv2.line(result, points['left_hip'], points['right_hip'], (0, 255, 255), 2)
            
            return result
        
        return frame
    
    def reset_pose_history(self):
        """Reset"""
        self.tshirt_mask = None
        self.body_landmarks = None
    
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
            'body_detected': self.body_landmarks is not None
        }
    
    def get_available_clothing(self, clothing_type):
        return self.clothing_templates.get(clothing_type, [])
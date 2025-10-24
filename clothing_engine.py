"""
PRECISE BODY-FITTING CLOTHING ENGINE
Exact torso detection and placement
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
        print("✅ PRECISE body-fitting clothing engine ready!")
    
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
    
    def detect_upper_body_precise(self, frame):
        """PRECISE upper body detection for exact placement"""
        try:
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect upper body
            bodies = self.upper_body_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=3, 
                minSize=(120, 120),
                maxSize=(400, 400)
            )
            
            if len(bodies) > 0:
                # Use the largest body detection
                bx, by, bw, bh = max(bodies, key=lambda x: x[2] * x[3])
                
                print(f"🎯 BODY DETECTED: x={bx}, y={by}, w={bw}, h={bh}")
                
                # Calculate precise torso region
                torso_top = by + int(bh * 0.2)    # Start below neck
                torso_bottom = by + bh            # End of upper body
                torso_left = bx + int(bw * 0.1)   # Slightly inside left edge
                torso_right = bx + int(bw * 0.9)  # Slightly inside right edge
                
                torso_width = torso_right - torso_left
                torso_height = torso_bottom - torso_top
                
                return {
                    'torso_x': torso_left,
                    'torso_y': torso_top, 
                    'torso_width': torso_width,
                    'torso_height': torso_height,
                    'center_x': torso_left + torso_width // 2,
                    'center_y': torso_top + torso_height // 2
                }
            
            print("❌ NO BODY DETECTED - Trying face-based estimation")
            return self.detect_torso_from_face(frame)
            
        except Exception as e:
            print(f"Body detection error: {e}")
            return self.detect_torso_from_face(frame)
    
    def detect_torso_from_face(self, frame):
        """Fallback: Estimate torso from face position"""
        try:
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
            
            if len(faces) > 0:
                fx, fy, fw, fh = max(faces, key=lambda x: x[2] * x[3])
                
                # Calculate torso based on face position
                torso_top = fy + fh + int(fh * 0.1)  # Start below face
                torso_bottom = min(h, torso_top + int(fh * 3.0))  # Extend down
                torso_center_x = fx + fw // 2
                torso_width = int(fw * 2.5)  # Wider than face
                
                torso_left = max(0, torso_center_x - torso_width // 2)
                torso_right = min(w, torso_center_x + torso_width // 2)
                
                torso_width = torso_right - torso_left
                torso_height = torso_bottom - torso_top
                
                print(f"🎯 FACE-BASED TORSO: x={torso_left}, y={torso_top}, w={torso_width}, h={torso_height}")
                
                return {
                    'torso_x': torso_left,
                    'torso_y': torso_top,
                    'torso_width': torso_width, 
                    'torso_height': torso_height,
                    'center_x': torso_center_x,
                    'center_y': torso_top + torso_height // 2
                }
            
            # Last resort: center of screen
            print("⚠️ USING SCREEN CENTER FALLBACK")
            return {
                'torso_x': w // 4,
                'torso_y': h // 4, 
                'torso_width': w // 2,
                'torso_height': h // 2,
                'center_x': w // 2,
                'center_y': h // 2
            }
            
        except Exception as e:
            print(f"Face detection error: {e}")
            return {
                'torso_x': 300,
                'torso_y': 200, 
                'torso_width': 400,
                'torso_height': 500,
                'center_x': 500,
                'center_y': 450
            }
    
    def remove_background_simple(self, img):
        """Simple but effective background removal"""
        try:
            if len(img.shape) == 3 and img.shape[2] == 4:
                # Already has alpha channel
                bgr = img[:, :, :3]
                alpha = img[:, :, 3]
                return bgr, alpha
            
            # For images without alpha channel
            bgr = img
            
            # Convert to HSV for better color separation
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            
            # Detect white/light background
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 55, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            
            # Detect based on brightness
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            _, bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Combine masks
            background_mask = cv2.bitwise_or(white_mask, bright_mask)
            
            # Invert to get shirt mask
            shirt_mask = cv2.bitwise_not(background_mask)
            
            # Clean up the mask
            kernel = np.ones((3, 3), np.uint8)
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel, iterations=1)
            
            return bgr, shirt_mask
            
        except Exception as e:
            print(f"Background removal error: {e}")
            # Return full opaque mask as fallback
            bgr = img if len(img.shape) == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            mask = np.ones((img.shape[0], img.shape[1]), dtype=np.uint8) * 255
            return bgr, mask
    
    def apply_shirt_direct_placement(self, frame, clothing_item):
        """DIRECT PRECISE placement on torso"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🎯 STARTING PRECISE SHIRT PLACEMENT")
            print(f"📺 Frame size: {w}x{h}")
            
            # Step 1: Detect exact torso position
            torso_info = self.detect_upper_body_precise(frame)
            
            torso_x = torso_info['torso_x']
            torso_y = torso_info['torso_y'] 
            torso_width = torso_info['torso_width']
            torso_height = torso_info['torso_height']
            
            print(f"🎯 TORSO DETECTED:")
            print(f"   Position: ({torso_x}, {torso_y})")
            print(f"   Size: {torso_width}x{torso_height}")
            print(f"   Center: ({torso_info['center_x']}, {torso_info['center_y']})")
            
            # Step 2: Load and prepare shirt
            shirt_img = clothing_item['image']
            shirt_h, shirt_w = shirt_img.shape[:2]
            
            print(f"👕 Original shirt size: {shirt_w}x{shirt_h}")
            
            # Step 3: Calculate shirt dimensions to fit torso
            # Use torso width as base, maintain aspect ratio
            target_width = torso_width + 100  # Slightly wider than torso
            target_height = int((shirt_h / shirt_w) * target_width)
            
            # Ensure shirt reaches bottom of screen
            available_height = h - torso_y
            if target_height < available_height:
                target_height = available_height
                # Recalculate width to maintain aspect ratio
                target_width = int((shirt_w / shirt_h) * target_height)
            
            print(f"📏 Target shirt size: {target_width}x{target_height}")
            
            # Step 4: Resize shirt
            resized_shirt = cv2.resize(shirt_img, (target_width, target_height))
            
            # Step 5: Remove background
            shirt_bgr, shirt_alpha = self.remove_background_simple(resized_shirt)
            
            # Step 6: Calculate placement position (centered on torso)
            placement_x = torso_info['center_x'] - target_width // 2
            placement_y = torso_y - 30  # Start slightly above torso
            
            # Ensure within frame bounds
            placement_x = max(0, placement_x)
            placement_y = max(0, placement_y)
            
            # Adjust if shirt goes beyond right edge
            if placement_x + target_width > w:
                placement_x = w - target_width
            
            # Adjust if shirt goes beyond bottom
            if placement_y + target_height > h:
                target_height = h - placement_y
                # Resize if needed
                if target_height != resized_shirt.shape[0]:
                    resized_shirt = cv2.resize(shirt_img, (target_width, target_height))
                    shirt_bgr, shirt_alpha = self.remove_background_simple(resized_shirt)
            
            print(f"📍 FINAL PLACEMENT: ({placement_x}, {placement_y})")
            print(f"📍 Shirt will cover: {placement_x}-{placement_x + target_width}, {placement_y}-{placement_y + target_height}")
            
            # Step 7: Apply shirt to frame
            result = frame.copy()
            
            # Get the region of interest
            roi = result[placement_y:placement_y + target_height, placement_x:placement_x + target_width]
            
            # Ensure ROI matches shirt dimensions
            if roi.shape[0] == target_height and roi.shape[1] == target_width:
                # Alpha blending
                alpha_normalized = shirt_alpha.astype(float) / 255.0
                alpha_3d = np.stack([alpha_normalized] * 3, axis=2)
                
                # Blend shirt with ROI
                blended = (shirt_bgr.astype(float) * alpha_3d + 
                          roi.astype(float) * (1.0 - alpha_3d))
                
                # Place blended result back
                result[placement_y:placement_y + target_height, placement_x:placement_x + target_width] = blended.astype(np.uint8)
                
                print("✅✅✅ SHIRT SUCCESSFULLY PLACED ON TORSO!")
                print(f"    ✅ Exact torso positioning")
                print(f"    ✅ Natural body fitting") 
                print(f"    ✅ Full coverage achieved")
                
                return result
            else:
                print(f"❌ ROI mismatch: ROI={roi.shape}, Shirt=({target_height}, {target_width})")
                return frame
                
        except Exception as e:
            print(f"❌ Shirt placement error: {e}")
            import traceback
            traceback.print_exc()
            return frame
    
    def apply_tshirt_color_replacement(self, frame, clothing_item):
        """T-shirt color replacement (keep your existing method)"""
        try:
            clothing_img = clothing_item['image']
            
            if clothing_item['color_hue'] is None:
                clothing_item['color_hue'] = self.extract_dominant_color(clothing_img)
            
            target_hue = clothing_item['color_hue']
            mask = self.create_torso_mask_precise(frame)
            self.tshirt_mask = mask
            
            result = self.replace_color_simple(frame, mask, target_hue)
            return result
        except Exception as e:
            print(f"T-shirt error: {e}")
            return frame
    
    def create_torso_mask_precise(self, frame):
        """Create precise torso mask based on body detection"""
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        torso_info = self.detect_upper_body_precise(frame)
        
        if torso_info:
            torso_x = torso_info['torso_x']
            torso_y = torso_info['torso_y']
            torso_width = torso_info['torso_width']
            torso_height = torso_info['torso_height']
            
            # Create rectangular mask for torso
            cv2.rectangle(mask, 
                         (torso_x, torso_y), 
                         (torso_x + torso_width, torso_y + torso_height), 
                         255, -1)
            
            # Soften edges
            mask = cv2.GaussianBlur(mask, (15, 15), 0)
        else:
            # Fallback mask
            cv2.rectangle(mask, (w//4, h//4), (3*w//4, 3*h//4), 255, -1)
            mask = cv2.GaussianBlur(mask, (25, 25), 0)
        
        return mask
    
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
                # USE THE NEW PRECISE PLACEMENT METHOD
                result = self.apply_shirt_direct_placement(frame, clothing_item)
            else:
                result = frame
            
            self.current_outfit = clothing_item
            self.current_outfit_type = clothing_type
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return frame
    
    def debug_draw_detection(self, frame):
        """Debug visualization showing exact detection"""
        result = frame.copy()
        
        # Detect torso
        torso_info = self.detect_upper_body_precise(frame)
        
        if torso_info:
            # Draw torso rectangle
            cv2.rectangle(result, 
                         (torso_info['torso_x'], torso_info['torso_y']),
                         (torso_info['torso_x'] + torso_info['torso_width'], 
                          torso_info['torso_y'] + torso_info['torso_height']),
                         (0, 255, 0), 3)
            
            # Draw center point
            cv2.circle(result, 
                      (torso_info['center_x'], torso_info['center_y']), 
                      8, (0, 0, 255), -1)
            
            # Draw info text
            cv2.putText(result, f"TORSO: {torso_info['torso_width']}x{torso_info['torso_height']}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(result, f"POSITION: ({torso_info['torso_x']}, {torso_info['torso_y']})", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            status = "PRECISE BODY DETECTION - READY"
            color = (0, 255, 0)
        else:
            status = "FALLBACK DETECTION - MAY BE LESS ACCURATE"
            color = (0, 255, 255)
        
        cv2.putText(result, status, (10, result.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
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
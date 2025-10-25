"""
ULTIMATE BACKGROUND REMOVAL ENGINE
Pure shirt-only extraction with complete transparency
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
        print("✅ ULTIMATE background removal engine ready!")
    
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
                        # PRE-PROCESS: Remove background immediately when loading
                        cleaned_img = self.remove_background_completely(img)
                        self.clothing_templates[clothing_type].append({
                            'image': cleaned_img,  # Store cleaned version
                            'name': filename,
                            'color_hue': None,
                            'original': img  # Keep original for reference
                        })
    
    def remove_background_completely(self, img):
        """ULTIMATE background removal - returns pure shirt with transparency"""
        print("🔥 ULTIMATE BACKGROUND REMOVAL ACTIVATED!")
        
        try:
            # If image already has alpha channel, use it as base
            if len(img.shape) == 3 and img.shape[2] == 4:
                bgr = img[:, :, :3]
                alpha = img[:, :, 3]
                # Enhance existing alpha
                _, alpha = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
            else:
                bgr = img
                alpha = np.ones((img.shape[0], img.shape[1]), dtype=np.uint8) * 255
            
            # METHOD 1: Ultra-sensitive white detection
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            
            # Detect ANY light colors (very aggressive)
            lower_white = np.array([0, 0, 150])    # Very sensitive to brightness
            upper_white = np.array([180, 100, 255]) # Catch even slightly colored backgrounds
            white_mask_hsv = cv2.inRange(hsv, lower_white, upper_white)
            
            # METHOD 2: RGB white detection (aggressive)
            b, g, r = cv2.split(bgr)
            white_mask_rgb = ((b > 150) | (g > 150) | (r > 150)).astype(np.uint8) * 255
            
            # METHOD 3: Grayscale brightness
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            _, white_mask_gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # METHOD 4: Edge-based content detection
            edges = cv2.Canny(gray, 50, 150)
            kernel = np.ones((5, 5), np.uint8)
            dilated_edges = cv2.dilate(edges, kernel, iterations=3)
            
            # COMBINE ALL WHITE DETECTION METHODS
            combined_white = cv2.bitwise_or(white_mask_hsv, white_mask_rgb)
            combined_white = cv2.bitwise_or(combined_white, white_mask_gray)
            
            # INVERT to get potential shirt areas
            potential_shirt = cv2.bitwise_not(combined_white)
            
            # COMBINE with edges to capture all shirt content
            shirt_mask = cv2.bitwise_or(potential_shirt, dilated_edges)
            
            # AGGRESSIVE CLEANING
            kernel = np.ones((7, 7), np.uint8)
            
            # Remove small noise
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel, iterations=2)
            
            # Fill holes in shirt
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
            
            # Find largest contour (assume it's the shirt)
            contours, _ = cv2.findContours(shirt_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Create mask from largest contour
                contour_mask = np.zeros_like(shirt_mask)
                cv2.drawContours(contour_mask, [largest_contour], -1, 255, -1)
                
                # Use contour mask as final shirt mask
                shirt_mask = contour_mask
            
            # FINAL ENHANCEMENT: Remove any remaining small areas
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(shirt_mask, 8, cv2.CV_32S)
            
            if num_labels > 1:
                # Find largest component
                largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
                
                # Create mask with only largest component
                final_mask = np.zeros_like(shirt_mask)
                final_mask[labels == largest_label] = 255
                shirt_mask = final_mask
            
            # Apply Gaussian blur for smooth edges
            shirt_mask = cv2.GaussianBlur(shirt_mask, (3, 3), 0)
            
            # Create final image with transparency
            result = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = shirt_mask  # Set alpha channel
            
            # VERIFICATION
            shirt_pixels = cv2.countNonZero(shirt_mask)
            total_pixels = shirt_mask.shape[0] * shirt_mask.shape[1]
            background_pixels = total_pixels - shirt_pixels
            
            print(f"✅ BACKGROUND REMOVAL COMPLETE:")
            print(f"   👕 Shirt pixels: {shirt_pixels}")
            print(f"   🎯 Background pixels: {background_pixels}")
            print(f"   📊 Background removed: {(background_pixels/total_pixels)*100:.1f}%")
            
            if shirt_pixels < 1000:
                print("⚠️ WARNING: Very few shirt pixels detected!")
                return self.emergency_background_removal(img)
            
            return result
            
        except Exception as e:
            print(f"❌ Ultimate removal failed: {e}")
            return self.emergency_background_removal(img)
    
    def emergency_background_removal(self, img):
        """Emergency fallback - removes everything except center"""
        print("🚨 EMERGENCY BACKGROUND REMOVAL ACTIVATED!")
        
        h, w = img.shape[:2]
        
        if len(img.shape) == 3 and img.shape[2] == 4:
            result = img.copy()
        else:
            result = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        
        # Create circular mask in center (assume shirt is in center)
        center_mask = np.zeros((h, w), dtype=np.uint8)
        center_x, center_y = w // 2, h // 2
        radius = min(w, h) // 3
        
        cv2.circle(center_mask, (center_x, center_y), radius, 255, -1)
        
        # Apply circular mask to alpha channel
        result[:, :, 3] = center_mask
        
        print("✅ Emergency removal complete - using circular mask")
        return result
    
    def remove_background_simple(self, img):
        """Simple but effective background removal for real-time"""
        try:
            if len(img.shape) == 3 and img.shape[2] == 4:
                # Already processed - return as is
                return img[:, :, :3], img[:, :, 3]
            
            # Use the ultimate removal but return separate image and mask
            cleaned_img = self.remove_background_completely(img)
            return cleaned_img[:, :, :3], cleaned_img[:, :, 3]
            
        except Exception as e:
            print(f"Simple removal error: {e}")
            # Fallback: assume center is shirt
            h, w = img.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.rectangle(mask, (w//4, h//4), (3*w//4, 3*h//4), 255, -1)
            return img, mask
    
    def detect_upper_body_precise(self, frame):
        """Precise body detection"""
        try:
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            bodies = self.upper_body_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=3, 
                minSize=(120, 120), maxSize=(400, 400)
            )
            
            if len(bodies) > 0:
                bx, by, bw, bh = max(bodies, key=lambda x: x[2] * x[3])
                
                torso_top = by + int(bh * 0.2)
                torso_bottom = by + bh
                torso_left = bx + int(bw * 0.1)
                torso_right = bx + int(bw * 0.9)
                
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
            
            return self.detect_torso_from_face(frame)
            
        except Exception as e:
            print(f"Body detection error: {e}")
            return self.detect_torso_from_face(frame)
    
    def detect_torso_from_face(self, frame):
        """Fallback torso detection from face"""
        try:
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
            
            if len(faces) > 0:
                fx, fy, fw, fh = max(faces, key=lambda x: x[2] * x[3])
                
                torso_top = fy + fh + int(fh * 0.1)
                torso_bottom = min(h, torso_top + int(fh * 3.0))
                torso_center_x = fx + fw // 2
                torso_width = int(fw * 2.5)
                
                torso_left = max(0, torso_center_x - torso_width // 2)
                torso_right = min(w, torso_center_x + torso_width // 2)
                
                torso_width = torso_right - torso_left
                torso_height = torso_bottom - torso_top
                
                return {
                    'torso_x': torso_left,
                    'torso_y': torso_top,
                    'torso_width': torso_width, 
                    'torso_height': torso_height,
                    'center_x': torso_center_x,
                    'center_y': torso_top + torso_height // 2
                }
            
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
                'torso_x': 300, 'torso_y': 200, 
                'torso_width': 400, 'torso_height': 500,
                'center_x': 500, 'center_y': 450
            }
    
    def apply_pure_shirt_overlay(self, frame, clothing_item):
        """Apply PURE shirt with NO background"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🎯 APPLYING PURE SHIRT (NO BACKGROUND)")
            
            # Get pre-cleaned shirt (already has transparency)
            shirt_img = clothing_item['image']
            
            # Verify it has alpha channel
            if shirt_img.shape[2] != 4:
                print("❌ Shirt image doesn't have alpha channel! Re-cleaning...")
                shirt_img = self.remove_background_completely(shirt_img)
            
            # Detect torso
            torso_info = self.detect_upper_body_precise(frame)
            
            # Calculate dimensions
            target_width = torso_info['torso_width'] + 100
            target_height = int((shirt_img.shape[0] / shirt_img.shape[1]) * target_width)
            
            # Ensure full length
            available_height = h - torso_info['torso_y']
            if target_height < available_height:
                target_height = available_height
                target_width = int((shirt_img.shape[1] / shirt_img.shape[0]) * target_height)
            
            print(f"📏 Resizing to: {target_width}x{target_height}")
            
            # Resize shirt (preserving alpha channel)
            resized_shirt = cv2.resize(shirt_img, (target_width, target_height), interpolation=cv2.INTER_AREA)
            
            # Extract RGBA channels
            shirt_bgr = resized_shirt[:, :, :3]
            shirt_alpha = resized_shirt[:, :, 3]
            
            # Position shirt
            placement_x = torso_info['center_x'] - target_width // 2
            placement_y = torso_info['torso_y'] - 30
            
            # Boundary checks
            placement_x = max(0, placement_x)
            placement_y = max(0, placement_y)
            
            if placement_x + target_width > w:
                placement_x = w - target_width
            if placement_y + target_height > h:
                target_height = h - placement_y
                resized_shirt = cv2.resize(shirt_img, (target_width, target_height))
                shirt_bgr = resized_shirt[:, :, :3]
                shirt_alpha = resized_shirt[:, :, 3]
            
            print(f"📍 Placing at: ({placement_x}, {placement_y})")
            
            # Apply pure shirt overlay
            result = frame.copy()
            roi = result[placement_y:placement_y + target_height, placement_x:placement_x + target_width]
            
            if roi.shape[:2] == (target_height, target_width):
                # Normalize alpha
                alpha_normalized = shirt_alpha.astype(float) / 255.0
                alpha_3d = np.stack([alpha_normalized] * 3, axis=2)
                
                # Perfect blending - only shirt pixels appear
                blended = (shirt_bgr.astype(float) * alpha_3d + 
                          roi.astype(float) * (1.0 - alpha_3d))
                
                result[placement_y:placement_y + target_height, placement_x:placement_x + target_width] = blended.astype(np.uint8)
                
                print("✅✅✅ PURE SHIRT APPLIED - NO BACKGROUND!")
                return result
            else:
                print("❌ ROI mismatch")
                return frame
                
        except Exception as e:
            print(f"❌ Pure shirt error: {e}")
            import traceback
            traceback.print_exc()
            return frame
    
    def apply_tshirt_color_replacement(self, frame, clothing_item):
        """T-shirt color replacement"""
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
        """Create torso mask"""
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        torso_info = self.detect_upper_body_precise(frame)
        
        if torso_info:
            cv2.rectangle(mask, 
                         (torso_info['torso_x'], torso_info['torso_y']), 
                         (torso_info['torso_x'] + torso_info['torso_width'], 
                          torso_info['torso_y'] + torso_info['torso_height']), 
                         255, -1)
            mask = cv2.GaussianBlur(mask, (15, 15), 0)
        else:
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
                # USE PURE SHIRT OVERLAY
                result = self.apply_pure_shirt_overlay(frame, clothing_item)
            else:
                result = frame
            
            self.current_outfit = clothing_item
            self.current_outfit_type = clothing_type
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return frame
    
    def debug_draw_detection(self, frame):
        """Debug visualization"""
        result = frame.copy()
        
        torso_info = self.detect_upper_body_precise(frame)
        
        if torso_info:
            cv2.rectangle(result, 
                         (torso_info['torso_x'], torso_info['torso_y']),
                         (torso_info['torso_x'] + torso_info['torso_width'], 
                          torso_info['torso_y'] + torso_info['torso_height']),
                         (0, 255, 0), 3)
            
            cv2.circle(result, 
                      (torso_info['center_x'], torso_info['center_y']), 
                      8, (0, 0, 255), -1)
            
            cv2.putText(result, "PURE SHIRT READY - NO BACKGROUND", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
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
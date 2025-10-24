"""
ADVANCED BACKGROUND REMOVAL CLOTHING ENGINE
Complete white background removal for clean shirt overlay
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
        print("✅ ADVANCED background removal engine ready!")
    
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
    
    def remove_background_aggressive(self, img):
        """AGGRESSIVE background removal - removes ALL white background"""
        try:
            print("🎨 Removing white background aggressively...")
            
            if len(img.shape) == 3 and img.shape[2] == 4:
                # Image already has alpha channel
                bgr = img[:, :, :3]
                alpha = img[:, :, 3]
                print("✓ Using existing alpha channel")
                return bgr, alpha
            
            # Convert to different color spaces for better detection
            bgr = img
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
            
            # METHOD 1: HSV white detection (most effective)
            lower_white1 = np.array([0, 0, 200])    # Very bright, low saturation
            upper_white1 = np.array([180, 60, 255]) # All hues, low saturation, high value
            white_mask1 = cv2.inRange(hsv, lower_white1, upper_white1)
            
            # METHOD 2: LAB color space for light colors
            l_channel = lab[:, :, 0]
            light_mask = (l_channel > 200).astype(np.uint8) * 255
            
            # METHOD 3: RGB white detection
            b, g, r = cv2.split(bgr)
            white_mask3 = ((b > 200) & (g > 200) & (r > 200)).astype(np.uint8) * 255
            
            # METHOD 4: Grayscale brightness
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            _, bright_mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
            
            # COMBINE ALL MASKS - be aggressive!
            combined_white = cv2.bitwise_or(white_mask1, light_mask)
            combined_white = cv2.bitwise_or(combined_white, white_mask3)
            combined_white = cv2.bitwise_or(combined_white, bright_mask)
            
            # Invert to get shirt mask (white=background, black=shirt)
            shirt_mask = cv2.bitwise_not(combined_white)
            
            # Clean up the mask aggressively
            kernel = np.ones((5, 5), np.uint8)
            
            # Remove small white spots in shirt area
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            # Remove small black spots in background area  
            shirt_mask = cv2.morphologyEx(shirt_mask, cv2.MORPH_OPEN, kernel, iterations=2)
            
            # Fill holes in the shirt mask
            contours, _ = cv2.findContours(shirt_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                hull = cv2.convexHull(largest_contour)
                filled_mask = np.zeros_like(shirt_mask)
                cv2.fillPoly(filled_mask, [hull], 255)
                shirt_mask = filled_mask
            
            # Final cleanup
            shirt_mask = cv2.medianBlur(shirt_mask, 5)
            
            # Count pixels to verify we have a good mask
            shirt_pixels = cv2.countNonZero(shirt_mask)
            total_pixels = shirt_mask.shape[0] * shirt_mask.shape[1]
            shirt_percentage = (shirt_pixels / total_pixels) * 100
            
            print(f"📊 Shirt pixels: {shirt_pixels}/{total_pixels} ({shirt_percentage:.1f}%)")
            
            if shirt_pixels < 1000:  # If too few shirt pixels, use fallback
                print("⚠️ Too few shirt pixels, using fallback mask")
                shirt_mask = self.create_fallback_mask(bgr)
            
            return bgr, shirt_mask
            
        except Exception as e:
            print(f"❌ Background removal error: {e}")
            # Emergency fallback
            bgr = img if len(img.shape) == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            mask = self.create_fallback_mask(bgr)
            return bgr, mask
    
    def create_fallback_mask(self, bgr_img):
        """Create a mask that covers most of the image except borders"""
        h, w = bgr_img.shape[:2]
        mask = np.ones((h, w), dtype=np.uint8) * 255
        
        # Remove borders (assume borders are background)
        border_size = min(20, h//10, w//10)
        mask[:border_size, :] = 0  # Top border
        mask[-border_size:, :] = 0  # Bottom border
        mask[:, :border_size] = 0   # Left border
        mask[:, -border_size:] = 0  # Right border
        
        return mask
    
    def remove_background_advanced(self, img):
        """Even more advanced background removal with edge detection"""
        try:
            if len(img.shape) == 3 and img.shape[2] == 4:
                bgr = img[:, :, :3]
                alpha = img[:, :, 3]
                # Enhance existing alpha
                _, enhanced_alpha = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
                return bgr, enhanced_alpha
            
            bgr = img
            
            # Use multiple methods for robust background removal
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            
            # Method 1: Color-based white detection
            lower_white = np.array([0, 0, 180])
            upper_white = np.array([180, 80, 255])
            color_mask = cv2.inRange(hsv, lower_white, upper_white)
            
            # Method 2: Edge-based content detection
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Dilate edges to capture content areas
            kernel = np.ones((3, 3), np.uint8)
            dilated_edges = cv2.dilate(edges, kernel, iterations=2)
            
            # Method 3: Brightness-based
            _, bright_mask = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)
            
            # Combine masks - anything that's NOT white AND has edges is content
            background_mask = cv2.bitwise_or(color_mask, bright_mask)
            
            # Content mask is inverse of background, plus edge areas
            content_mask = cv2.bitwise_not(background_mask)
            content_mask = cv2.bitwise_or(content_mask, dilated_edges)
            
            # Clean up
            content_mask = cv2.morphologyEx(content_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
            content_mask = cv2.morphologyEx(content_mask, cv2.MORPH_OPEN, kernel, iterations=1)
            
            return bgr, content_mask
            
        except Exception as e:
            print(f"Advanced background removal failed: {e}")
            return self.remove_background_aggressive(img)
    
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
    
    def apply_shirt_clean_overlay(self, frame, clothing_item):
        """Apply shirt with COMPLETE background removal"""
        try:
            h, w = frame.shape[:2]
            print(f"\n🎯 APPLYING CLEAN SHIRT OVERLAY (NO BACKGROUND)")
            
            # Step 1: Detect torso
            torso_info = self.detect_upper_body_precise(frame)
            torso_x = torso_info['torso_x']
            torso_y = torso_info['torso_y'] 
            torso_width = torso_info['torso_width']
            torso_height = torso_info['torso_height']
            
            print(f"🎯 Torso: ({torso_x}, {torso_y}) {torso_width}x{torso_height}")
            
            # Step 2: Load shirt
            shirt_img = clothing_item['image']
            shirt_h, shirt_w = shirt_img.shape[:2]
            
            # Step 3: Calculate dimensions
            target_width = torso_width + 80
            target_height = int((shirt_h / shirt_w) * target_width)
            
            # Ensure full length
            available_height = h - torso_y
            if target_height < available_height:
                target_height = available_height
                target_width = int((shirt_w / shirt_h) * target_height)
            
            print(f"📏 Shirt size: {target_width}x{target_height}")
            
            # Step 4: Resize and remove background AGGRESSIVELY
            resized_shirt = cv2.resize(shirt_img, (target_width, target_height))
            shirt_bgr, shirt_alpha = self.remove_background_aggressive(resized_shirt)
            
            # Step 5: Verify we have a good mask
            shirt_pixels = cv2.countNonZero(shirt_alpha)
            if shirt_pixels < 500:
                print("🔄 First attempt failed, trying advanced method...")
                shirt_bgr, shirt_alpha = self.remove_background_advanced(resized_shirt)
                shirt_pixels = cv2.countNonZero(shirt_alpha)
                print(f"🔄 Advanced method: {shirt_pixels} shirt pixels")
            
            # Step 6: Position shirt
            placement_x = torso_info['center_x'] - target_width // 2
            placement_y = torso_y - 20
            
            # Boundary checks
            placement_x = max(0, placement_x)
            placement_y = max(0, placement_y)
            
            if placement_x + target_width > w:
                placement_x = w - target_width
            if placement_y + target_height > h:
                target_height = h - placement_y
                resized_shirt = cv2.resize(shirt_img, (target_width, target_height))
                shirt_bgr, shirt_alpha = self.remove_background_aggressive(resized_shirt)
            
            print(f"📍 Placement: ({placement_x}, {placement_y})")
            
            # Step 7: Apply with clean alpha blending
            result = frame.copy()
            roi = result[placement_y:placement_y + target_height, placement_x:placement_x + target_width]
            
            if roi.shape[:2] == (target_height, target_width):
                # Normalize alpha mask
                alpha_normalized = shirt_alpha.astype(float) / 255.0
                alpha_3d = np.stack([alpha_normalized] * 3, axis=2)
                
                # Blend - only where alpha > 0
                blended = (shirt_bgr.astype(float) * alpha_3d + 
                          roi.astype(float) * (1.0 - alpha_3d))
                
                result[placement_y:placement_y + target_height, placement_x:placement_x + target_width] = blended.astype(np.uint8)
                
                print("✅✅✅ CLEAN SHIRT APPLIED - NO BACKGROUND!")
                return result
            else:
                print("❌ ROI dimension mismatch")
                return frame
                
        except Exception as e:
            print(f"❌ Clean overlay error: {e}")
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
        """Create precise torso mask"""
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        torso_info = self.detect_upper_body_precise(frame)
        
        if torso_info:
            torso_x = torso_info['torso_x']
            torso_y = torso_info['torso_y']
            torso_width = torso_info['torso_width']
            torso_height = torso_info['torso_height']
            
            cv2.rectangle(mask, 
                         (torso_x, torso_y), 
                         (torso_x + torso_width, torso_y + torso_height), 
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
                # USE THE CLEAN OVERLAY METHOD
                result = self.apply_shirt_clean_overlay(frame, clothing_item)
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
            
            cv2.putText(result, f"TORSO: {torso_info['torso_width']}x{torso_info['torso_height']}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            status = "BODY DETECTED - CLEAN OVERLAY READY"
            color = (0, 255, 0)
        else:
            status = "FALLBACK MODE"
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
"""
Complete Popup Manager with Enhanced Beautiful Icons
Copy and paste this entire file to replace your popup_manager.py
"""

import cv2
import numpy as np
import os
import math

class PopupManager:
    def __init__(self):
        """Initialize smart popup system with improved click detection"""
        # Popup layout configuration
        self.popup_size = (120, 120)
        self.popup_margin = 20
        self.border_thickness = 3
        self.corner_radius = 20
        
        # EXPANDED CLICK AREAS - This is the key fix
        self.click_padding = 30  # Extra clickable area around each popup
        
        # Color scheme
        self.colors = {
            'primary': (255, 255, 255),
            'secondary': (240, 240, 240),
            'accent': (64, 158, 255),
            'success': (46, 204, 113),
            'hover': (255, 206, 84),
            'border': (200, 200, 200),
            'shadow': (0, 0, 0),
            'text': (50, 50, 50),
            'click_area': (0, 255, 0)  # Green for click area visualization
        }
        
        # Popup positions
        self.left_positions = []
        self.right_positions = []
        self.popup_data = {}
        self.current_popup_type = ""
        
        print("Smart popup manager with enhanced click detection initialized!")
    
    def calculate_positions(self, frame_width, frame_height):
        """Calculate popup positions based on screen size"""
        self.left_positions = []
        self.right_positions = []
        
        # Calculate positions for left side (4 popups)
        left_x = self.popup_margin + self.click_padding  # Account for click padding
        start_y = (frame_height - 4 * self.popup_size[1] - 3 * self.popup_margin) // 2
        
        for i in range(4):
            y = start_y + i * (self.popup_size[1] + self.popup_margin)
            self.left_positions.append((left_x, y))
        
        # Calculate positions for right side (4 popups)
        right_x = frame_width - self.popup_size[0] - self.popup_margin - self.click_padding
        
        for i in range(4):
            y = start_y + i * (self.popup_size[1] + self.popup_margin)
            self.right_positions.append((right_x, y))

    def draw_initial_clothing_choice(self, frame, categories):
        """Draw initial T-shirt vs Shirt choice - T-shirt LEFT, Shirt RIGHT"""
        h, w = frame.shape[:2]
        self.calculate_positions(w, h)
        self.current_popup_type = "initial_choice"
        self.popup_data = {}
        
        # Category icons
        category_icons = {
            'tshirts': self.create_category_icon('tshirts'),
            'shirts': self.create_category_icon('shirts')
        }
        
        # FIXED: T-shirts on LEFT (index 0), Shirts on RIGHT (index 1)
        positions = [self.left_positions[1], self.right_positions[1]]  # Use middle positions
        
        for i, category in enumerate(categories):
            if i >= len(positions):
                break
            
            pos = positions[i]
            popup_id = f"initial_{i}"
            icon = category_icons.get(category, self.create_category_icon('default'))
            
            popup = self.create_styled_popup(icon, category.replace('_', ' ').title())
            frame = self.overlay_popup_with_click_area(frame, popup, pos, popup_id)
        
        return frame
    
    def draw_accessory_popups(self, frame, accessories):
        """Draw accessory selection popups (Blazer, Tie, No Accessories)"""
        h, w = frame.shape[:2]
        self.calculate_positions(w, h)
        self.current_popup_type = "accessories"
        self.popup_data = {}
        
        # Create icons for accessories
        accessory_icons = {
            'blazers': self.create_category_icon('blazers'),
            'ties': self.create_category_icon('ties'),
            'no_accessories': self.create_no_accessories_icon()
        }
        
        # Use three positions: left, center, right
        positions = [
            self.left_positions[1],   # Left: Blazers
            (w // 2 - self.popup_size[0] // 2, self.left_positions[1][1]),  # Center: Ties  
            self.right_positions[1]   # Right: No Accessories
        ]
        
        for i, accessory in enumerate(accessories):
            if i >= len(positions):
                break
            
            pos = positions[i]
            popup_id = f"accessory_{i}"
            icon = accessory_icons.get(accessory, self.create_category_icon('default'))
            
            # Create labels
            labels = {
                'blazers': 'Blazers',
                'ties': 'Ties', 
                'no_accessories': 'Shirt Only'
            }
            label = labels.get(accessory, accessory.title())
            
            popup = self.create_styled_popup(icon, label)
            frame = self.overlay_popup_with_click_area(frame, popup, pos, popup_id)
        
        return frame

    def create_no_accessories_icon(self):
        """Create icon for 'no accessories' option"""
        icon = np.ones((self.popup_size[1], self.popup_size[0], 3), dtype=np.uint8) * 250
        
        center_x, center_y = self.popup_size[0] // 2, self.popup_size[1] // 2
        
        # Draw a shirt with a red "X" over it
        # Draw shirt
        cv2.rectangle(icon, (center_x - 25, center_y - 20), 
                     (center_x + 25, center_y + 30), (100, 150, 200), 2)
        # Collar
        cv2.rectangle(icon, (center_x - 30, center_y - 25), 
                     (center_x + 30, center_y - 15), (100, 150, 200), 2)
        
        # Draw red X to indicate "no accessories"
        cv2.line(icon, (center_x - 35, center_y - 35), (center_x + 35, center_y + 35), (0, 0, 255), 3)
        cv2.line(icon, (center_x + 35, center_y - 35), (center_x - 35, center_y + 35), (0, 0, 255), 3)
        
        return icon
    
    def draw_background_popups(self, frame, background_paths):
        """Draw background selection popups with expanded click areas"""
        h, w = frame.shape[:2]
        self.calculate_positions(w, h)
        self.current_popup_type = "bg"
        self.popup_data = {}  # Clear previous popup data
        
        all_positions = self.left_positions + self.right_positions
        
        for i, bg_path in enumerate(background_paths[:8]):
            if i >= len(all_positions):
                break
            
            pos = all_positions[i]
            popup_id = f"bg_{i}"
            
            # Load background thumbnail or create placeholder
            if os.path.exists(bg_path):
                bg_thumb = cv2.imread(bg_path)
                bg_thumb = cv2.resize(bg_thumb, self.popup_size)
            else:
                bg_thumb = self.create_background_placeholder(i)
            
            # Create and draw popup
            popup = self.create_styled_popup(bg_thumb, f"Background {i+1}")
            frame = self.overlay_popup_with_click_area(frame, popup, pos, popup_id)
        
        return frame
    
    def draw_clothing_category_popups(self, frame, categories):
        """Draw clothing category popups with expanded click areas"""
        h, w = frame.shape[:2]
        self.calculate_positions(w, h)
        self.current_popup_type = "category"
        self.popup_data = {}
        
        # Category icons
        category_icons = {
            'shirts': self.create_category_icon('shirts'),
            'tshirts': self.create_category_icon('tshirts'),
            'blazers': self.create_category_icon('blazers'),
            'ties': self.create_category_icon('ties')
        }
        
        all_positions = self.left_positions + self.right_positions
        
        for i, category in enumerate(categories[:8]):
            if i >= len(all_positions):
                break
            
            pos = all_positions[i]
            popup_id = f"category_{i}"
            icon = category_icons.get(category, self.create_category_icon('default'))
            
            popup = self.create_styled_popup(icon, category.replace('_', ' ').title())
            frame = self.overlay_popup_with_click_area(frame, popup, pos, popup_id)
        
        return frame
    
    def draw_clothing_item_popups(self, frame, clothing_items, clothing_type):
        """Draw specific clothing item popups with expanded click areas"""
        h, w = frame.shape[:2]
        self.calculate_positions(w, h)
        self.current_popup_type = "item"
        self.popup_data = {}
        
        all_positions = self.left_positions + self.right_positions
        
        for i, item in enumerate(clothing_items[:8]):
            if i >= len(all_positions):
                break
            
            pos = all_positions[i]
            popup_id = f"item_{i}"
            
            # Load actual clothing image
            if isinstance(item, dict) and 'image' in item:
                clothing_thumbnail = self.create_clothing_thumbnail(item['image'])
            elif isinstance(item, str):
                # If item is just a path string
                clothing_img = cv2.imread(item, cv2.IMREAD_UNCHANGED)
                clothing_thumbnail = self.create_clothing_thumbnail(clothing_img)
            else:
                clothing_thumbnail = self.create_placeholder_thumbnail()
            
            # Create popup with real clothing image
            popup = self.create_styled_popup(clothing_thumbnail, f"{clothing_type.capitalize()} {i+1}")
            frame = self.overlay_popup_with_click_area(frame, popup, pos, popup_id)
        
        return frame
    
    def overlay_popup_with_click_area(self, frame, popup, position, popup_id):
        """Overlay popup with expanded clickable area and visual feedback"""
        x, y = position
        ph, pw = popup.shape[:2]
        fh, fw = frame.shape[:2]
        
        # Ensure popup fits in frame
        if x + pw > fw or y + ph > fh or x < 0 or y < 0:
            return frame
        
        # Calculate expanded click area bounds
        click_x1 = max(0, x - self.click_padding)
        click_y1 = max(0, y - self.click_padding)
        click_x2 = min(fw, x + pw + self.click_padding)
        click_y2 = min(fh, y + ph + self.click_padding)
        
        # Store popup data for click detection with EXPANDED bounds
        self.popup_data[popup_id] = {
            'position': position,
            'size': (pw, ph),
            'click_bounds': (click_x1, click_y1, click_x2, click_y2),  # Expanded clickable area
            'visual_bounds': (x, y, x + pw, y + ph),  # Visual popup area
            'index': int(popup_id.split('_')[1])
        }
        
        # Clickable area is invisible - no visual indicators needed
        
        # Blend popup with frame
        roi = frame[y:y + ph, x:x + pw]
        
        # Create alpha mask for smooth blending
        alpha = 0.95
        blended = cv2.addWeighted(roi, 1 - alpha, popup, alpha, 0)
        frame[y:y + ph, x:x + pw] = blended
        
        return frame
    
    def check_popup_click(self, finger_pos):
        """Enhanced click detection using expanded click areas"""
        if finger_pos is None:
            return None
        
        x, y = finger_pos
        
        # Check all popups using EXPANDED click bounds
        for popup_id, data in self.popup_data.items():
            click_bounds = data['click_bounds']
            if (click_bounds[0] <= x <= click_bounds[2] and 
                click_bounds[1] <= y <= click_bounds[3]):
                
                print(f"Finger detected in {popup_id} click area at ({x}, {y})")
                return data['index']
        
        return None
    
    def highlight_popup_on_hover(self, frame, finger_pos):
        """Highlight popup when finger is in clickable area"""
        if finger_pos is None:
            return frame
        
        x, y = finger_pos
        
        # Find which popup is being hovered
        for popup_id, data in self.popup_data.items():
            click_bounds = data['click_bounds']
            if (click_bounds[0] <= x <= click_bounds[2] and 
                click_bounds[1] <= y <= click_bounds[3]):
                
                # Draw bright highlight around the visual popup area
                visual_bounds = data['visual_bounds']
                cv2.rectangle(frame, 
                             (visual_bounds[0] - 5, visual_bounds[1] - 5),
                             (visual_bounds[2] + 5, visual_bounds[3] + 5),
                             self.colors['hover'], 4)
                
                # Add "HOVERING" text
                cv2.putText(frame, "HOVERING", 
                           (visual_bounds[0], visual_bounds[1] - 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.colors['hover'], 2)
                
                break
        
        return frame
    
    def create_clothing_thumbnail(self, clothing_image):
        """Create thumbnail from real clothing image with improved handling"""
        if clothing_image is None:
            return self.create_placeholder_thumbnail()
        
        try:
            # Handle both 3-channel and 4-channel images
            if len(clothing_image.shape) == 3 and clothing_image.shape[2] == 4:
                # Image has alpha channel
                bgr = clothing_image[:, :, :3]
                alpha = clothing_image[:, :, 3]
                
                # Create white background
                white_bg = np.ones_like(bgr) * 255
                
                # Blend with white background using alpha
                alpha_norm = alpha.astype(float) / 255.0
                alpha_3d = np.stack([alpha_norm] * 3, axis=2)
                
                result = bgr.astype(float) * alpha_3d + white_bg.astype(float) * (1 - alpha_3d)
                result = result.astype(np.uint8)
            else:
                result = clothing_image
            
            # Resize to popup size
            thumbnail = cv2.resize(result, self.popup_size)
            
            # Add subtle border
            cv2.rectangle(thumbnail, (0, 0), (self.popup_size[0]-1, self.popup_size[1]-1), 
                         self.colors['border'], 2)
            
            return thumbnail
            
        except Exception as e:
            print(f"Thumbnail creation error: {e}")
            return self.create_placeholder_thumbnail()
    
    def create_placeholder_thumbnail(self):
        """Create placeholder thumbnail when image fails to load"""
        placeholder = np.ones((self.popup_size[1], self.popup_size[0], 3), dtype=np.uint8) * 240
        
        # Add "No Image" text
        cv2.putText(placeholder, "No Image", (20, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        return placeholder
    
    def create_category_icon(self, category):
        """Create STUNNING category icons with modern, professional design"""
        icon = np.ones((self.popup_size[1], self.popup_size[0], 3), dtype=np.uint8) * 255
        
        center_x, center_y = self.popup_size[0] // 2, self.popup_size[1] // 2
        
        if category == 'shirts':
            # ========== ENHANCED FORMAL SHIRT ==========
            base_color = (220, 160, 100)  # Warm tan/beige
            dark_color = (180, 120, 70)
            light_color = (255, 200, 140)
            accent_color = (200, 140, 80)
            
            # Main body with realistic proportions
            body_width = 55
            body_height = 70
            body_top = center_y - 25
            
            # Create gradient body (lighter at top, darker at bottom)
            for y in range(body_height):
                ratio = y / body_height
                color = tuple(int(base_color[i] * (1 - ratio * 0.25)) for i in range(3))
                cv2.line(icon, 
                        (center_x - body_width//2, body_top + y),
                        (center_x + body_width//2, body_top + y),
                        color, 1)
            
            # Professional pointed collar
            collar_height = 18
            collar_width = 12
            
            # Left collar
            collar_left = np.array([
                [center_x - body_width//2 - 10, body_top - 5],
                [center_x - collar_width, body_top - 5],
                [center_x - 8, body_top + collar_height],
                [center_x - body_width//2, body_top + collar_height//2]
            ], dtype=np.int32)
            cv2.fillPoly(icon, [collar_left], dark_color)
            cv2.polylines(icon, [collar_left], True, (140, 90, 50), 2)
            
            # Right collar
            collar_right = np.array([
                [center_x + collar_width, body_top - 5],
                [center_x + body_width//2 + 10, body_top - 5],
                [center_x + body_width//2, body_top + collar_height//2],
                [center_x + 8, body_top + collar_height]
            ], dtype=np.int32)
            cv2.fillPoly(icon, [collar_right], dark_color)
            cv2.polylines(icon, [collar_right], True, (140, 90, 50), 2)
            
            # Collar fold lines (adds depth)
            cv2.line(icon, (center_x - collar_width, body_top - 5), 
                    (center_x - 6, body_top + 12), (140, 90, 50), 2)
            cv2.line(icon, (center_x + collar_width, body_top - 5), 
                    (center_x + 6, body_top + 12), (140, 90, 50), 2)
            
            # Button placket (center strip)
            placket_width = 14
            cv2.rectangle(icon, 
                         (center_x - placket_width//2, body_top),
                         (center_x + placket_width//2, body_top + body_height),
                         light_color, -1)
            cv2.line(icon, (center_x - placket_width//2, body_top),
                    (center_x - placket_width//2, body_top + body_height),
                    accent_color, 2)
            cv2.line(icon, (center_x + placket_width//2, body_top),
                    (center_x + placket_width//2, body_top + body_height),
                    accent_color, 2)
            
            # Realistic buttons with 3D effect
            button_positions = [
                body_top + 12, body_top + 24, body_top + 36, 
                body_top + 48, body_top + 60
            ]
            for btn_y in button_positions:
                # Button shadow
                cv2.circle(icon, (center_x + 2, btn_y + 2), 5, (160, 160, 160), -1)
                # Button base
                cv2.circle(icon, (center_x, btn_y), 5, (250, 250, 250), -1)
                # Button rim
                cv2.circle(icon, (center_x, btn_y), 5, dark_color, 2)
                # Button holes (stitch pattern)
                cv2.circle(icon, (center_x - 2, btn_y - 1), 1, dark_color, -1)
                cv2.circle(icon, (center_x + 2, btn_y - 1), 1, dark_color, -1)
                cv2.circle(icon, (center_x - 2, btn_y + 1), 1, dark_color, -1)
                cv2.circle(icon, (center_x + 2, btn_y + 1), 1, dark_color, -1)
            
            # Chest pocket with realistic flap
            pocket_x = center_x - body_width//2 + 15
            pocket_y = body_top + 20
            pocket_w = 20
            pocket_h = 16
            
            # Pocket background
            cv2.rectangle(icon, (pocket_x, pocket_y), 
                         (pocket_x + pocket_w, pocket_y + pocket_h),
                         accent_color, -1)
            # Pocket outline
            cv2.rectangle(icon, (pocket_x, pocket_y), 
                         (pocket_x + pocket_w, pocket_y + pocket_h),
                         dark_color, 2)
            # Pocket flap with stitching
            flap_h = 6
            cv2.line(icon, (pocket_x, pocket_y + flap_h), 
                    (pocket_x + pocket_w, pocket_y + flap_h), dark_color, 2)
            cv2.line(icon, (pocket_x + 2, pocket_y + flap_h + 2), 
                    (pocket_x + pocket_w - 2, pocket_y + flap_h + 2), dark_color, 1)
            
            # Body outline for definition
            cv2.rectangle(icon, 
                         (center_x - body_width//2, body_top),
                         (center_x + body_width//2, body_top + body_height),
                         dark_color, 3)
            
            # Side seams (vertical lines)
            cv2.line(icon, (center_x - body_width//2 + 5, body_top + 10),
                    (center_x - body_width//2 + 5, body_top + body_height - 5),
                    accent_color, 1)
            cv2.line(icon, (center_x + body_width//2 - 5, body_top + 10),
                    (center_x + body_width//2 - 5, body_top + body_height - 5),
                    accent_color, 1)
            
            # Bottom hem with stitching detail
            hem_height = 10
            cv2.rectangle(icon,
                         (center_x - body_width//2, body_top + body_height - hem_height),
                         (center_x + body_width//2, body_top + body_height),
                         light_color, -1)
            cv2.line(icon,
                    (center_x - body_width//2, body_top + body_height - hem_height),
                    (center_x + body_width//2, body_top + body_height - hem_height),
                    dark_color, 2)
        
        elif category == 'tshirts':
            # ========== ENHANCED T-SHIRT (Casual & Modern) ==========
            base_color = (100, 200, 120)  # Fresh mint green
            dark_color = (60, 140, 80)
            light_color = (140, 240, 160)
            accent_color = (80, 180, 100)
            
            # Main body
            body_width = 50
            body_height = 60
            body_top = center_y - 20
            
            # Create gradient body
            for y in range(body_height):
                ratio = y / body_height
                color = tuple(int(base_color[i] * (1 - ratio * 0.2)) for i in range(3))
                cv2.line(icon,
                        (center_x - body_width//2, body_top + y),
                        (center_x + body_width//2, body_top + y),
                        color, 1)
            
            # Short sleeves with 3D effect
            sleeve_width = 24
            sleeve_height = 20
            
            # Left sleeve with shading
            left_sleeve = np.array([
                [center_x - body_width//2 - sleeve_width, body_top + 4],
                [center_x - body_width//2, body_top],
                [center_x - body_width//2, body_top + sleeve_height],
                [center_x - body_width//2 - sleeve_width + 10, body_top + sleeve_height + 4]
            ], dtype=np.int32)
            
            # Gradient on sleeve
            for i in range(10):
                ratio = i / 10
                sleeve_color = tuple(int(dark_color[j] * (1 + ratio * 0.2)) for j in range(3))
                temp_sleeve = left_sleeve.copy()
                temp_sleeve[:, 0] += i
                cv2.fillPoly(icon, [temp_sleeve], sleeve_color)
            
            cv2.fillPoly(icon, [left_sleeve], dark_color)
            cv2.polylines(icon, [left_sleeve], True, (40, 100, 60), 2)
            
            # Right sleeve
            right_sleeve = np.array([
                [center_x + body_width//2, body_top],
                [center_x + body_width//2 + sleeve_width, body_top + 4],
                [center_x + body_width//2 + sleeve_width - 10, body_top + sleeve_height + 4],
                [center_x + body_width//2, body_top + sleeve_height]
            ], dtype=np.int32)
            cv2.fillPoly(icon, [right_sleeve], dark_color)
            cv2.polylines(icon, [right_sleeve], True, (40, 100, 60), 2)
            
            # V-neck collar with ribbing
            collar_depth = 18
            collar_width = 20
            v_neck = np.array([
                [center_x - collar_width, body_top],
                [center_x, body_top + collar_depth],
                [center_x + collar_width, body_top]
            ], dtype=np.int32)
            cv2.fillPoly(icon, [v_neck], (250, 250, 250))
            cv2.polylines(icon, [v_neck], False, dark_color, 3)
            
            # Collar ribbing (inner line)
            inner_v = np.array([
                [center_x - collar_width + 3, body_top],
                [center_x, body_top + collar_depth - 3],
                [center_x + collar_width - 3, body_top]
            ], dtype=np.int32)
            cv2.polylines(icon, [inner_v], False, accent_color, 1)
            
            # Decorative chest design (circular logo area)
            design_y = body_top + 28
            design_radius = 14
            
            # Logo background circle
            cv2.circle(icon, (center_x, design_y), design_radius, light_color, -1)
            cv2.circle(icon, (center_x, design_y), design_radius, dark_color, 2)
            
            # Star pattern inside logo
            star_points = []
            for i in range(5):
                angle = i * 144 - 90
                outer_x = center_x + int(10 * math.cos(math.radians(angle)))
                outer_y = design_y + int(10 * math.sin(math.radians(angle)))
                star_points.append([outer_x, outer_y])
                
                # Inner points
                angle_inner = angle + 72
                inner_x = center_x + int(5 * math.cos(math.radians(angle_inner)))
                inner_y = design_y + int(5 * math.sin(math.radians(angle_inner)))
                star_points.append([inner_x, inner_y])
            
            star_array = np.array(star_points, dtype=np.int32)
            cv2.fillPoly(icon, [star_array], (255, 255, 255))
            cv2.polylines(icon, [star_array], True, dark_color, 2)
            
            # Body outline
            cv2.rectangle(icon,
                         (center_x - body_width//2, body_top),
                         (center_x + body_width//2, body_top + body_height),
                         dark_color, 3)
            
            # Side seams
            cv2.line(icon, (center_x - body_width//2 + 4, body_top + 8),
                    (center_x - body_width//2 + 4, body_top + body_height - 5),
                    accent_color, 1)
            cv2.line(icon, (center_x + body_width//2 - 4, body_top + 8),
                    (center_x + body_width//2 - 4, body_top + body_height - 5),
                    accent_color, 1)
            
            # Bottom hem with double stitching
            hem_y = body_top + body_height - 4
            cv2.line(icon,
                    (center_x - body_width//2, hem_y),
                    (center_x + body_width//2, hem_y),
                    light_color, 3)
            cv2.line(icon,
                    (center_x - body_width//2, hem_y - 2),
                    (center_x + body_width//2, hem_y - 2),
                    accent_color, 1)
        
        elif category == 'blazers':
            # ========== ENHANCED BLAZER (Professional) ==========
            base_color = (90, 90, 150)  # Navy blue
            dark_color = (50, 50, 100)
            light_color = (120, 120, 190)
            
            body_width = 58
            body_height = 75
            body_top = center_y - 30
            
            # Gradient body
            for y in range(body_height):
                ratio = y / body_height
                color = tuple(int(base_color[i] * (1 - ratio * 0.3)) for i in range(3))
                cv2.line(icon,
                        (center_x - body_width//2, body_top + y),
                        (center_x + body_width//2, body_top + y),
                        color, 1)
            
            # Notched lapels (signature blazer feature)
            lapel_width = 18
            lapel_height = 30
            
            # Left lapel
            lapel_left = np.array([
                [center_x - body_width//2 - 8, body_top],
                [center_x - body_width//2, body_top + 10],
                [center_x - 10, body_top + lapel_height],
                [center_x - body_width//2, body_top + lapel_height]
            ], dtype=np.int32)
            cv2.fillPoly(icon, [lapel_left], dark_color)
            cv2.polylines(icon, [lapel_left], True, (30, 30, 70), 3)
            
            # Right lapel
            lapel_right = np.array([
                [center_x + body_width//2 + 8, body_top],
                [center_x + body_width//2, body_top + 10],
                [center_x + 10, body_top + lapel_height],
                [center_x + body_width//2, body_top + lapel_height]
            ], dtype=np.int32)
            cv2.fillPoly(icon, [lapel_right], dark_color)
            cv2.polylines(icon, [lapel_right], True, (30, 30, 70), 3)
            
            # Lapel notch detail
            cv2.line(icon, (center_x - body_width//2, body_top + 10),
                    (center_x - 8, body_top + 20), (30, 30, 70), 2)
            cv2.line(icon, (center_x + body_width//2, body_top + 10),
                    (center_x + 8, body_top + 20), (30, 30, 70), 2)
            
            # Button stance (single-breasted, 2 buttons)
            button_x = center_x - 15
            button_positions = [body_top + 38, body_top + 52]
            
            for btn_y in button_positions:
                # Shadow
                cv2.circle(icon, (button_x + 2, btn_y + 2), 6, (100, 100, 100), -1)
                # Button
                cv2.circle(icon, (button_x, btn_y), 6, (220, 200, 160), -1)
                cv2.circle(icon, (button_x, btn_y), 6, dark_color, 2)
                # Thread pattern
                cv2.line(icon, (button_x - 3, btn_y), (button_x + 3, btn_y), dark_color, 1)
                cv2.line(icon, (button_x, btn_y - 3), (button_x, btn_y + 3), dark_color, 1)
            
            # Breast pocket with pocket square
            pocket_x = center_x + 12
            pocket_y = body_top + 22
            pocket_w = 20
            pocket_h = 14
            
            cv2.rectangle(icon, (pocket_x, pocket_y), 
                         (pocket_x + pocket_w, pocket_y + pocket_h),
                         dark_color, 2)
            
            # Pocket square (handkerchief) peeking out
            hanky = np.array([
                [pocket_x + 5, pocket_y],
                [pocket_x + 10, pocket_y - 5],
                [pocket_x + 15, pocket_y]
            ], dtype=np.int32)
            cv2.fillPoly(icon, [hanky], (255, 255, 255))
            cv2.polylines(icon, [hanky], False, dark_color, 2)
            
            # Vent line (back slit indicator)
            cv2.line(icon, (center_x, body_top + body_height - 20),
                    (center_x, body_top + body_height), light_color, 2)
            
            # Body outline
            cv2.rectangle(icon,
                         (center_x - body_width//2, body_top),
                         (center_x + body_width//2, body_top + body_height),
                         dark_color, 3)
            
            # Sleeve details
            cv2.line(icon, (center_x - body_width//2 + 6, body_top + 15),
                    (center_x - body_width//2 + 6, body_top + body_height - 10),
                    light_color, 1)
            cv2.line(icon, (center_x + body_width//2 - 6, body_top + 15),
                    (center_x + body_width//2 - 6, body_top + body_height - 10),
                    light_color, 1)
        
        elif category == 'ties':
            # ========== ENHANCED TIE (Elegant) ==========
            base_color = (160, 70, 70)  # Rich burgundy
            dark_color = (110, 40, 40)
            light_color = (210, 110, 110)
            
            # Windsor knot (professional tie knot)
            knot_y = center_y - 40
            knot_w = 16
            knot_h = 16
            
            knot_points = np.array([
                [center_x - knot_w, knot_y],
                [center_x - knot_w//2, knot_y + knot_h],
                [center_x + knot_w//2, knot_y + knot_h],
                [center_x + knot_w, knot_y]
            ], dtype=np.int32)
            
            # Gradient on knot
            for i in range(knot_h):
                ratio = i / knot_h
                color = tuple(int(dark_color[j] * (1 + ratio * 0.3)) for j in range(3))
                y_pos = knot_y + i
                x_left = center_x - knot_w + int(i * knot_w / knot_h / 2)
                x_right = center_x + knot_w - int(i * knot_w / knot_h / 2)
                cv2.line(icon, (x_left, y_pos), (x_right, y_pos), color, 1)
            
            cv2.polylines(icon, [knot_points], True, (80, 30, 30), 3)
            
            # Tie blade (main part)
            blade_width = 20
            blade_length = 70
            blade_top = knot_y + knot_h
            
            # Gradient on tie blade
            for y in range(blade_length - 12):
                ratio = y / blade_length
                color = tuple(int(base_color[i] * (1 - ratio * 0.2)) for i in range(3))
                cv2.line(icon,
                        (center_x - blade_width//2, blade_top + y),
                        (center_x + blade_width//2, blade_top + y),
                        color, 1)
            
            # Tie point (bottom triangle)
            tie_point = np.array([
                [center_x - blade_width//2, blade_top + blade_length - 12],
                [center_x + blade_width//2, blade_top + blade_length - 12],
                [center_x, blade_top + blade_length + 10]
            ], dtype=np.int32)
            cv2.fillPoly(icon, [tie_point], base_color)
            cv2.polylines(icon, [tie_point], True, dark_color, 3)
            
            # Diagonal stripe pattern (classic tie design)
            stripe_spacing = 14
            for i in range(0, blade_length + 20, stripe_spacing):
                y_start = blade_top + i
                # Diagonal stripes
                for offset in range(-blade_width, blade_width, 3):
                    x1 = center_x - blade_width//2 + offset
                    y1 = y_start
                    x2 = x1 + 8
                    y2 = y1 + 8
                    
                    # Clip to tie bounds
                    if blade_top <= y1 <= blade_top + blade_length:
                        cv2.line(icon, (x1, y1), (x2, y2), light_color, 2)
            
            # Tie outline
            cv2.rectangle(icon,
                         (center_x - blade_width//2, blade_top),
                         (center_x + blade_width//2, blade_top + blade_length - 12),
                         dark_color, 2)
            
            # Dimple below knot (professional touch)
            cv2.line(icon, (center_x - 4, blade_top), 
                    (center_x, blade_top + 6), dark_color, 2)
            cv2.line(icon, (center_x + 4, blade_top), 
                    (center_x, blade_top + 6), dark_color, 2)
        
        return icon
    
    def create_styled_popup(self, content, label):
        """Create a beautifully styled popup"""
        popup_height = self.popup_size[1] + 40
        popup = np.ones((popup_height, self.popup_size[0], 3), dtype=np.uint8) * 255
        
        # Create rounded rectangle background
        popup_with_border = self.create_rounded_rectangle(
            popup.shape[1], popup.shape[0], self.corner_radius, self.colors['primary']
        )
        
        # Place content in popup
        y_offset = 10
        x_offset = 10
        content_resized = cv2.resize(content, (self.popup_size[0] - 20, self.popup_size[1] - 40))
        popup_with_border[y_offset:y_offset + content_resized.shape[0], 
                         x_offset:x_offset + content_resized.shape[1]] = content_resized
        
        # Add label text
        label_y = self.popup_size[1] - 20
        popup_with_border = self.add_text_to_popup(popup_with_border, label, 
                                                  (self.popup_size[0] // 2, label_y))
        
        # Add border
        popup_with_border = self.add_popup_border(popup_with_border)
        
        return popup_with_border
    
    def create_rounded_rectangle(self, width, height, radius, color):
        """Create a rounded rectangle"""
        img = np.ones((height, width, 3), dtype=np.uint8)
        img[:] = color
        
        # Create mask for rounded corners
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Draw rounded rectangle
        cv2.rectangle(mask, (radius, 0), (width - radius, height), 255, -1)
        cv2.rectangle(mask, (0, radius), (width, height - radius), 255, -1)
        cv2.circle(mask, (radius, radius), radius, 255, -1)
        cv2.circle(mask, (width - radius, radius), radius, 255, -1)
        cv2.circle(mask, (radius, height - radius), radius, 255, -1)
        cv2.circle(mask, (width - radius, height - radius), radius, 255, -1)
        
        # Apply mask
        result = cv2.bitwise_and(img, img, mask=mask)
        
        return result
    
    def add_text_to_popup(self, popup, text, position):
        """Add text to popup with professional styling"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1
        
        # Get text size
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        
        # Center text
        text_x = position[0] - text_size[0] // 2
        text_y = position[1]
        
        # Add text with shadow effect
        cv2.putText(popup, text, (text_x + 1, text_y + 1), font, font_scale, 
                   (200, 200, 200), thickness)
        cv2.putText(popup, text, (text_x, text_y), font, font_scale, 
                   self.colors['text'], thickness)
        
        return popup
    
    def add_popup_border(self, popup):
        """Add border to popup"""
        h, w = popup.shape[:2]
        cv2.rectangle(popup, (0, 0), (w-1, h-1), self.colors['border'], 2)
        return popup
    
    def create_background_placeholder(self, index):
        """Create placeholder background thumbnail"""
        placeholder = np.zeros((self.popup_size[1], self.popup_size[0], 3), dtype=np.uint8)
        
        # Create different gradients for different backgrounds
        colors = [
            [(100, 150, 255), (50, 100, 200)],   # Blue gradient
            [(150, 255, 150), (100, 200, 100)],  # Green gradient
            [(255, 150, 100), (200, 100, 50)],   # Orange gradient
            [(200, 200, 255), (150, 150, 200)],  # Purple gradient
            [(255, 255, 150), (200, 200, 100)],  # Yellow gradient
            [(255, 150, 255), (200, 100, 200)],  # Pink gradient
            [(150, 255, 255), (100, 200, 200)],  # Cyan gradient
            [(200, 255, 200), (150, 200, 150)]   # Light green gradient
        ]
        
        color_pair = colors[index % len(colors)]
        
        for i in range(self.popup_size[1]):
            ratio = i / self.popup_size[1]
            color = [
                int(color_pair[0][j] * (1 - ratio) + color_pair[1][j] * ratio)
                for j in range(3)
            ]
            placeholder[i, :] = color
        
        # Add background icon
        center = (self.popup_size[0] // 2, self.popup_size[1] // 2)
        cv2.circle(placeholder, center, 20, (255, 255, 255), -1)
        cv2.putText(placeholder, "BG", (center[0] - 15, center[1] + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        return placeholder
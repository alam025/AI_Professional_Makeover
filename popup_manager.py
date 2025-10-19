"""
Complete Popup Manager - Fixed positioning and added missing methods
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
        """Create category icons for clothing types"""
        icon = np.ones((self.popup_size[1], self.popup_size[0], 3), dtype=np.uint8) * 250
        
        center_x, center_y = self.popup_size[0] // 2, self.popup_size[1] // 2
        
        if category == 'shirts':
            # Draw dress shirt icon
            cv2.rectangle(icon, (center_x - 30, center_y - 25), 
                         (center_x + 30, center_y + 35), (100, 150, 200), 2)
            # Collar
            cv2.rectangle(icon, (center_x - 35, center_y - 30), 
                         (center_x + 35, center_y - 20), (100, 150, 200), 2)
            # Buttons
            for y in range(center_y - 10, center_y + 30, 10):
                cv2.circle(icon, (center_x, y), 2, (100, 150, 200), -1)
        
        elif category == 'tshirts':
            # Draw t-shirt icon
            cv2.rectangle(icon, (center_x - 25, center_y - 20), 
                         (center_x + 25, center_y + 30), (50, 100, 50), 2)
            # Sleeves
            cv2.rectangle(icon, (center_x - 35, center_y - 25), 
                         (center_x + 35, center_y - 10), (50, 100, 50), 2)
            # Neckline
            cv2.circle(icon, (center_x, center_y - 20), 8, (50, 100, 50), 2)
        
        elif category == 'blazers':
            # Draw blazer icon
            cv2.rectangle(icon, (center_x - 30, center_y - 25), 
                         (center_x + 30, center_y + 40), (50, 50, 100), 2)
            # Lapels
            cv2.line(icon, (center_x - 30, center_y - 10), 
                    (center_x, center_y + 5), (50, 50, 100), 2)
            cv2.line(icon, (center_x + 30, center_y - 10), 
                    (center_x, center_y + 5), (50, 50, 100), 2)
            # Buttons
            cv2.circle(icon, (center_x - 10, center_y + 15), 3, (50, 50, 100), -1)
        
        elif category == 'ties':
            # Draw tie icon
            cv2.rectangle(icon, (center_x - 8, center_y - 30), 
                         (center_x + 8, center_y + 30), (150, 50, 50), -1)
            # Tie knot
            cv2.circle(icon, (center_x, center_y - 25), 10, (150, 50, 50), -1)
            # Pattern
            for y in range(center_y - 20, center_y + 25, 8):
                cv2.line(icon, (center_x - 6, y), (center_x + 6, y + 4), (200, 100, 100), 1)
        
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
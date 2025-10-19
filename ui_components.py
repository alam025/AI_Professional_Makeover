"""
UI Components - Beautiful and professional user interface elements
"""

import cv2
import numpy as np
import time
import math

class UIComponents:
    def __init__(self):
        """Initialize UI components with professional styling"""
        # Color palette (modern and professional)
        self.colors = {
            'primary': (64, 158, 255),       # Blue
            'secondary': (108, 117, 125),    # Gray
            'success': (40, 167, 69),        # Green
            'warning': (255, 193, 7),        # Yellow
            'danger': (220, 53, 69),         # Red
            'light': (248, 249, 250),        # Light gray
            'dark': (52, 58, 64),            # Dark gray
            'white': (255, 255, 255),        # White
            'black': (0, 0, 0),              # Black
            'accent': (255, 107, 107)        # Coral
        }
        
        # Typography
        self.fonts = {
            'title': cv2.FONT_HERSHEY_SIMPLEX,
            'subtitle': cv2.FONT_HERSHEY_SIMPLEX,
            'body': cv2.FONT_HERSHEY_SIMPLEX,
            'caption': cv2.FONT_HERSHEY_SIMPLEX
        }
        
        self.font_scales = {
            'title': 2.0,
            'subtitle': 1.2,
            'body': 0.8,
            'caption': 0.6
        }
        
        # Animation properties
        self.animation_speed = 0.1
        self.pulse_amplitude = 0.3
        
        print("🎨 UI components initialized with professional styling!")
    
    def draw_welcome_screen(self, frame):
        """Draw animated welcome screen"""
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Semi-transparent overlay
        cv2.rectangle(overlay, (0, 0), (w, h), self.colors['dark'], -1)
        frame = cv2.addWeighted(frame, 0.3, overlay, 0.7, 0)
        
        # Title
        title = "AI Professional Makeover"
        title_size = cv2.getTextSize(title, self.fonts['title'], self.font_scales['title'], 3)[0]
        title_x = (w - title_size[0]) // 2
        title_y = h // 2 - 100
        
        # Animated title with glow effect
        for offset in range(3, 0, -1):
            alpha = 0.3 / offset
            glow_color = tuple(int(c * alpha) for c in self.colors['primary'])
            cv2.putText(frame, title, (title_x + offset, title_y + offset), 
                       self.fonts['title'], self.font_scales['title'], glow_color, 5)
        
        cv2.putText(frame, title, (title_x, title_y), 
                   self.fonts['title'], self.font_scales['title'], self.colors['white'], 3)
        
        # Subtitle
        subtitle = "Transform your video calls instantly"
        subtitle_size = cv2.getTextSize(subtitle, self.fonts['subtitle'], self.font_scales['subtitle'], 2)[0]
        subtitle_x = (w - subtitle_size[0]) // 2
        subtitle_y = title_y + 80
        
        cv2.putText(frame, subtitle, (subtitle_x, subtitle_y), 
                   self.fonts['subtitle'], self.font_scales['subtitle'], self.colors['light'], 2)
        
        # Animated loading indicator
        self.draw_loading_animation(frame, (w // 2, subtitle_y + 60))
        
        # Instructions
        instruction = "Initializing camera... Please wait"
        inst_size = cv2.getTextSize(instruction, self.fonts['body'], self.font_scales['body'], 1)[0]
        inst_x = (w - inst_size[0]) // 2
        inst_y = subtitle_y + 120
        
        cv2.putText(frame, instruction, (inst_x, inst_y), 
                   self.fonts['body'], self.font_scales['body'], self.colors['secondary'], 1)
        
        return frame
    
    def draw_face_outline(self, frame, face_box):
        """Draw professional face detection outline"""
        if face_box is None:
            return frame
        
        x, y, w, h = face_box
        
        # Draw rounded rectangle outline
        color = self.colors['success']
        thickness = 3
        corner_length = 30
        
        # Top-left corner
        cv2.line(frame, (x, y + corner_length), (x, y), color, thickness)
        cv2.line(frame, (x, y), (x + corner_length, y), color, thickness)
        
        # Top-right corner
        cv2.line(frame, (x + w - corner_length, y), (x + w, y), color, thickness)
        cv2.line(frame, (x + w, y), (x + w, y + corner_length), color, thickness)
        
        # Bottom-left corner
        cv2.line(frame, (x, y + h - corner_length), (x, y + h), color, thickness)
        cv2.line(frame, (x, y + h), (x + corner_length, y + h), color, thickness)
        
        # Bottom-right corner
        cv2.line(frame, (x + w - corner_length, y + h), (x + w, y + h), color, thickness)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_length), color, thickness)
        
        # Add face detected indicator
        indicator_text = "Face Detected ✓"
        text_size = cv2.getTextSize(indicator_text, self.fonts['body'], self.font_scales['body'], 2)[0]
        text_x = x + w // 2 - text_size[0] // 2
        text_y = y - 20
        
        if text_y > 20:
            # Background for text
            cv2.rectangle(frame, (text_x - 10, text_y - text_size[1] - 5), 
                         (text_x + text_size[0] + 10, text_y + 5), self.colors['success'], -1)
            cv2.putText(frame, indicator_text, (text_x, text_y), 
                       self.fonts['body'], self.font_scales['body'], self.colors['white'], 2)
        
        return frame
    
    def draw_detection_progress(self, frame, progress):
        """Draw face detection progress bar"""
        h, w = frame.shape[:2]
        
        # Progress bar dimensions
        bar_width = 300
        bar_height = 20
        bar_x = (w - bar_width) // 2
        bar_y = h - 100
        
        # Background
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                     self.colors['light'], -1)
        
        # Progress fill
        fill_width = int(bar_width * progress)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), 
                     self.colors['primary'], -1)
        
        # Border
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                     self.colors['dark'], 2)
        
        # Progress text
        progress_text = f"Detecting face... {int(progress * 100)}%"
        text_size = cv2.getTextSize(progress_text, self.fonts['body'], self.font_scales['body'], 1)[0]
        text_x = bar_x + (bar_width - text_size[0]) // 2
        text_y = bar_y - 10
        
        cv2.putText(frame, progress_text, (text_x, text_y), 
                   self.fonts['body'], self.font_scales['body'], self.colors['dark'], 1)
        
        return frame
    
    def draw_face_detection_guide(self, frame):
        """Draw face detection guidance"""
        h, w = frame.shape[:2]
        
        # Guide overlay
        overlay = frame.copy()
        
        # Draw face outline guide in center
        guide_size = 200
        guide_x = (w - guide_size) // 2
        guide_y = (h - guide_size) // 2
        
        # Dashed rectangle
        dash_length = 20
        gap_length = 10
        color = self.colors['warning']
        
        # Top line
        for x in range(guide_x, guide_x + guide_size, dash_length + gap_length):
            cv2.line(frame, (x, guide_y), (min(x + dash_length, guide_x + guide_size), guide_y), color, 3)
        
        # Bottom line
        for x in range(guide_x, guide_x + guide_size, dash_length + gap_length):
            cv2.line(frame, (x, guide_y + guide_size), 
                    (min(x + dash_length, guide_x + guide_size), guide_y + guide_size), color, 3)
        
        # Left line
        for y in range(guide_y, guide_y + guide_size, dash_length + gap_length):
            cv2.line(frame, (guide_x, y), (guide_x, min(y + dash_length, guide_y + guide_size)), color, 3)
        
        # Right line
        for y in range(guide_y, guide_y + guide_size, dash_length + gap_length):
            cv2.line(frame, (guide_x + guide_size, y), 
                    (guide_x + guide_size, min(y + dash_length, guide_y + guide_size)), color, 3)
        
        # Instructions
        instruction = "Please position your face in the frame"
        inst_size = cv2.getTextSize(instruction, self.fonts['subtitle'], self.font_scales['subtitle'], 2)[0]
        inst_x = (w - inst_size[0]) // 2
        inst_y = guide_y - 40
        
        cv2.putText(frame, instruction, (inst_x, inst_y), 
                   self.fonts['subtitle'], self.font_scales['subtitle'], self.colors['white'], 2)
        
        return frame
    
    def draw_finger_cursor(self, frame, finger_pos):
        """Draw animated finger cursor"""
        if finger_pos is None:
            return frame
        
        x, y = finger_pos
        
        # Animated cursor with pulse effect
        time_val = time.time()
        pulse = math.sin(time_val * 5) * self.pulse_amplitude + 1
        
        # Outer ring
        outer_radius = int(20 * pulse)
        cv2.circle(frame, (x, y), outer_radius, self.colors['primary'], 3)
        
        # Inner circle
        inner_radius = 8
        cv2.circle(frame, (x, y), inner_radius, self.colors['white'], -1)
        cv2.circle(frame, (x, y), inner_radius, self.colors['primary'], 2)
        
        # Crosshair
        cross_length = 15
        cv2.line(frame, (x - cross_length, y), (x + cross_length, y), self.colors['primary'], 2)
        cv2.line(frame, (x, y - cross_length), (x, y + cross_length), self.colors['primary'], 2)
        
        return frame
    
    def draw_instruction_text(self, frame, text, position):
        """Draw instruction text with background"""
        x, y = position
        
        # Get text size
        text_size = cv2.getTextSize(text, self.fonts['subtitle'], self.font_scales['subtitle'], 2)[0]
        
        # Center text
        text_x = x - text_size[0] // 2
        text_y = y
        
        # Background rectangle
        padding = 20
        bg_x1 = text_x - padding
        bg_y1 = text_y - text_size[1] - padding
        bg_x2 = text_x + text_size[0] + padding
        bg_y2 = text_y + padding
        
        # Draw background with rounded corners
        overlay = frame.copy()
        cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), self.colors['dark'], -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Draw text
        cv2.putText(frame, text, (text_x, text_y), 
                   self.fonts['subtitle'], self.font_scales['subtitle'], self.colors['white'], 2)
        
        return frame
    
    def draw_completion_screen(self, frame):
        """Draw completion screen with options"""
        h, w = frame.shape[:2]
        
        # Semi-transparent overlay at top
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 150), self.colors['success'], -1)
        frame = cv2.addWeighted(frame, 0.8, overlay, 0.2, 0)
        
        # Completion message
        title = "✨ Professional Look Complete! ✨"
        title_size = cv2.getTextSize(title, self.fonts['title'], 1.2, 3)[0]
        title_x = (w - title_size[0]) // 2
        title_y = 60
        
        cv2.putText(frame, title, (title_x, title_y), 
                   self.fonts['title'], 1.2, self.colors['white'], 3)
        
        # Instructions
        instruction = "Point and click anywhere to save screenshot • Press 'R' to restart • Press 'Q' to quit"
        inst_size = cv2.getTextSize(instruction, self.fonts['body'], self.font_scales['body'], 1)[0]
        inst_x = (w - inst_size[0]) // 2
        inst_y = 100
        
        cv2.putText(frame, instruction, (inst_x, inst_y), 
                   self.fonts['body'], self.font_scales['body'], self.colors['white'], 1)
        
        # Add save button area (visual indicator)
        self.draw_save_button(frame, (w - 200, h - 100))
        
        return frame
    
    def draw_save_button(self, frame, position):
        """Draw save button"""
        x, y = position
        button_width = 150
        button_height = 50
        
        # Button background
        cv2.rectangle(frame, (x, y), (x + button_width, y + button_height), self.colors['primary'], -1)
        cv2.rectangle(frame, (x, y), (x + button_width, y + button_height), self.colors['dark'], 2)
        
        # Button text
        text = "📸 Save Photo"
        text_size = cv2.getTextSize(text, self.fonts['body'], self.font_scales['body'], 1)[0]
        text_x = x + (button_width - text_size[0]) // 2
        text_y = y + (button_height + text_size[1]) // 2
        
        cv2.putText(frame, text, (text_x, text_y), 
                   self.fonts['body'], self.font_scales['body'], self.colors['white'], 1)
        
        return frame
    
    def draw_loading_animation(self, frame, center):
        """Draw animated loading spinner"""
        x, y = center
        radius = 30
        time_val = time.time()
        
        # Rotating dots
        num_dots = 8
        for i in range(num_dots):
            angle = (time_val * 3 + i * 2 * math.pi / num_dots) % (2 * math.pi)
            dot_x = int(x + radius * math.cos(angle))
            dot_y = int(y + radius * math.sin(angle))
            
            # Fade effect
            alpha = (math.sin(time_val * 3 + i * 2 * math.pi / num_dots) + 1) / 2
            color = tuple(int(c * alpha) for c in self.colors['primary'])
            
            cv2.circle(frame, (dot_x, dot_y), 6, color, -1)
        
        return frame
    
    def create_gradient_background(self, width, height, gradient_type=0):
        """Create gradient background for placeholders"""
        background = np.zeros((height, width, 3), dtype=np.uint8)
        
        gradients = [
            # Professional gradients
            [(240, 248, 255), (176, 196, 222)],  # Light blue
            [(250, 240, 230), (205, 133, 63)],   # Warm brown
            [(245, 245, 245), (169, 169, 169)],  # Gray
            [(240, 255, 240), (144, 238, 144)],  # Light green
            [(255, 240, 245), (219, 112, 147)],  # Pink
            [(240, 255, 255), (175, 238, 238)],  # Cyan
            [(255, 250, 240), (255, 218, 185)],  # Peach
            [(248, 248, 255), (230, 230, 250)]   # Lavender
        ]
        
        start_color, end_color = gradients[gradient_type % len(gradients)]
        
        for y in range(height):
            ratio = y / height
            color = [
                int(start_color[i] * (1 - ratio) + end_color[i] * ratio)
                for i in range(3)
            ]
            background[y, :] = color
        
        return background
    
    def draw_step_indicator(self, frame, current_step, total_steps):
        """Draw step progress indicator"""
        h, w = frame.shape[:2]
        
        # Position at top of screen
        indicator_y = 30
        step_width = 40
        step_spacing = 60
        total_width = total_steps * step_spacing
        start_x = (w - total_width) // 2
        
        for i in range(total_steps):
            step_x = start_x + i * step_spacing
            
            if i < current_step:
                # Completed step
                cv2.circle(frame, (step_x, indicator_y), 15, self.colors['success'], -1)
                cv2.putText(frame, "✓", (step_x - 8, indicator_y + 5), 
                           self.fonts['body'], 0.6, self.colors['white'], 2)
            elif i == current_step:
                # Current step
                cv2.circle(frame, (step_x, indicator_y), 15, self.colors['primary'], -1)
                cv2.putText(frame, str(i + 1), (step_x - 6, indicator_y + 5), 
                           self.fonts['body'], 0.6, self.colors['white'], 2)
            else:
                # Future step
                cv2.circle(frame, (step_x, indicator_y), 15, self.colors['secondary'], -1)
                cv2.putText(frame, str(i + 1), (step_x - 6, indicator_y + 5), 
                           self.fonts['body'], 0.6, self.colors['white'], 2)
            
            # Connection line
            if i < total_steps - 1:
                cv2.line(frame, (step_x + 15, indicator_y), (step_x + step_spacing - 15, indicator_y), 
                        self.colors['secondary'], 2)
        
        return frame
    
    def draw_notification(self, frame, message, notification_type="info"):
        """Draw notification popup"""
        h, w = frame.shape[:2]
        
        # Notification colors
        type_colors = {
            'info': self.colors['primary'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['danger']
        }
        
        color = type_colors.get(notification_type, self.colors['primary'])
        
        # Notification dimensions
        notif_height = 60
        notif_width = min(len(message) * 12 + 40, w - 40)
        notif_x = (w - notif_width) // 2
        notif_y = 20
        
        # Background with shadow
        shadow_offset = 3
        cv2.rectangle(frame, (notif_x + shadow_offset, notif_y + shadow_offset), 
                     (notif_x + notif_width + shadow_offset, notif_y + notif_height + shadow_offset), 
                     (0, 0, 0), -1)
        
        # Main notification
        cv2.rectangle(frame, (notif_x, notif_y), (notif_x + notif_width, notif_y + notif_height), 
                     color, -1)
        cv2.rectangle(frame, (notif_x, notif_y), (notif_x + notif_width, notif_y + notif_height), 
                     self.colors['white'], 2)
        
        # Message text
        text_size = cv2.getTextSize(message, self.fonts['body'], self.font_scales['body'], 1)[0]
        text_x = notif_x + (notif_width - text_size[0]) // 2
        text_y = notif_y + (notif_height + text_size[1]) // 2
        
        cv2.putText(frame, message, (text_x, text_y), 
                   self.fonts['body'], self.font_scales['body'], self.colors['white'], 1)
        
        return frame
    
    def add_professional_watermark(self, frame):
        """Add subtle professional watermark"""
        h, w = frame.shape[:2]
        
        # Watermark text
        watermark = "AI Professional Makeover"
        font_scale = 0.5
        thickness = 1
        
        # Position at bottom right
        text_size = cv2.getTextSize(watermark, self.fonts['caption'], font_scale, thickness)[0]
        text_x = w - text_size[0] - 20
        text_y = h - 20
        
        # Semi-transparent background
        bg_padding = 5
        overlay = frame.copy()
        cv2.rectangle(overlay, (text_x - bg_padding, text_y - text_size[1] - bg_padding), 
                     (text_x + text_size[0] + bg_padding, text_y + bg_padding), 
                     self.colors['dark'], -1)
        
        frame = cv2.addWeighted(frame, 0.9, overlay, 0.1, 0)
        
        # Watermark text
        cv2.putText(frame, watermark, (text_x, text_y), 
                   self.fonts['caption'], font_scale, self.colors['light'], thickness)
        
        return frame
    
    def draw_fps_counter(self, frame, fps):
        """Draw FPS counter for performance monitoring"""
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(frame, fps_text, (10, 30), 
                   self.fonts['caption'], self.font_scales['caption'], self.colors['success'], 1)
        
        return frame
    
    def create_modern_button(self, width, height, text, color_scheme='primary'):
        """Create modern button graphics"""
        button = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Button color
        bg_color = self.colors.get(color_scheme, self.colors['primary'])
        
        # Rounded rectangle
        cv2.rectangle(button, (5, 5), (width - 5, height - 5), bg_color, -1)
        
        # Text
        text_size = cv2.getTextSize(text, self.fonts['body'], self.font_scales['body'], 2)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        
        cv2.putText(button, text, (text_x, text_y), 
                   self.fonts['body'], self.font_scales['body'], self.colors['white'], 2)
        
        return button
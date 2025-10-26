"""
COMPLETE AI PROFESSIONAL MAKEOVER APPLICATION
- Face detection
- Background selection  
- Hybrid clothing system (T-shirt HSV + Shirt overlay)
- Professional UI
"""

import cv2
import numpy as np
import os
import time
from camera_handler import CameraHandler
from gesture_detector import GestureDetector
from popup_manager import PopupManager
from background_engine import BackgroundEngine
from clothing_engine import ProfessionalClothingEngine
from ui_components import UIComponents

class ProfessionalMakeoverApp:
    def __init__(self):
        print("\n" + "="*70)
        print("🚀 AI PROFESSIONAL MAKEOVER - INITIALIZING")
        print("="*70)
        
        try:
            # Initialize all components
            print("📷 Initializing camera system...")
            self.camera = CameraHandler()
            
            print("👆 Initializing gesture detection...")
            self.gesture_detector = GestureDetector()
            
            print("🎨 Initializing UI components...")
            self.popup_manager = PopupManager()
            self.ui = UIComponents()
            
            print("🖼️  Initializing background engine...")
            self.bg_engine = BackgroundEngine()
            
            print("👔 Initializing hybrid clothing engine...")
            self.clothing_engine = ProfessionalClothingEngine()
            
            # Application state
            self.current_step = "welcome"
            self.face_detected_time = 0
            self.selected_background = None
            self.selected_clothing_type = None
            self.selected_clothing_item = None
            
            # Performance monitoring
            self.frame_count = 0
            self.fps_history = []
            self.current_fps = 0
            
            # Smart frame processing
            self.process_clothing_every_n = 2
            self.last_clothing_frame = None
            
            # Load assets
            print("📁 Loading application assets...")
            self.load_assets()
            
            print("\n✅ INITIALIZATION COMPLETE!")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            import traceback
            traceback.print_exc()
    
    def load_assets(self):
        """Load all application assets"""
        os.makedirs("assets/backgrounds", exist_ok=True)
        os.makedirs("assets/clothing/shirts", exist_ok=True)
        os.makedirs("assets/clothing/tshirts", exist_ok=True)
        os.makedirs("assets/clothing/blazers", exist_ok=True)
        os.makedirs("assets/clothing/ties", exist_ok=True)
        
        self.backgrounds = [
            "assets/backgrounds/office_modern.jpg",
            "assets/backgrounds/conference_room.jpg", 
            "assets/backgrounds/home_office.jpg",
            "assets/backgrounds/library.jpg",
            "assets/backgrounds/city_view.jpg",
            "assets/backgrounds/minimalist_white.jpg",
            "assets/backgrounds/tech_office.jpg",
            "assets/backgrounds/boardroom.jpg"
        ]
        
        self.create_placeholder_assets()
        print(f"   ✓ Loaded {len(self.backgrounds)} backgrounds")
    
    def create_placeholder_assets(self):
        """Create placeholder backgrounds if needed"""
        for i, bg_path in enumerate(self.backgrounds):
            if not os.path.exists(bg_path):
                img = self.ui.create_gradient_background(1280, 720, i)
                cv2.imwrite(bg_path, img)
    
    def run(self):
        """Main application loop"""
        print("🎥 Starting Professional Makeover System...")
        print("\n🎮 KEYBOARD CONTROLS:")
        print("   Q / ESC - Quit application")
        print("   R       - Restart from beginning")
        print("   C       - Capture Screenshot")
        print("\n")
        
        # Create borderless fullscreen window (no title bar)
        window_name = 'AI Professional Makeover'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        while True:
            try:
                frame_start_time = time.time()
                self.frame_count += 1
                
                # Get camera frame
                frame = self.camera.get_frame()
                if frame is None:
                    print("❌ Camera error!")
                    break
                
                # Resize for consistent processing
                frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_LINEAR)
                
                # Get gesture input
                finger_pos, is_clicking = self.gesture_detector.detect_finger_click(frame)
                
                # Process based on current step
                if self.current_step == "welcome":
                    frame = self.handle_welcome_screen(frame)
                    
                elif self.current_step == "face_detection":
                    frame = self.handle_face_detection(frame)
                    
                elif self.current_step == "background_selection":
                    frame = self.handle_background_selection(frame, finger_pos, is_clicking)
                    
                elif self.current_step == "clothing_selection":
                    frame = self.handle_clothing_selection(frame, finger_pos, is_clicking)
                    
                elif self.current_step == "complete":
                    frame = self.handle_complete_screen(frame, finger_pos, is_clicking)
                
                # Draw finger cursor
                if finger_pos and self.gesture_detector.calibrated:
                    frame = self.ui.draw_finger_cursor(frame, finger_pos)
                
                # Display frame
                cv2.imshow(window_name, frame)
                
                # Calculate FPS
                frame_time = time.time() - frame_start_time
                self.fps_history.append(1.0 / frame_time if frame_time > 0 else 30)
                if len(self.fps_history) > 30:
                    self.fps_history.pop(0)
                self.current_fps = int(np.mean(self.fps_history))
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break
                elif key == ord('r'):
                    self.restart_application()
                elif key == ord('c'):
                    self.capture_screenshot(frame)
                elif key == ord(' '):
                    if self.current_step == "welcome":
                        self.current_step = "face_detection"
                        print("🎬 Starting face detection...")
                
            except Exception as e:
                print(f"❌ Main loop error: {e}")
                import traceback
                traceback.print_exc()
                break
        
        self.cleanup()
    
    def handle_welcome_screen(self, frame):
        """Welcome screen with instructions"""
        frame = self.ui.draw_welcome_screen(frame)
        
        # Auto-start after 5 seconds
        if not hasattr(self, 'welcome_start_time'):
            self.welcome_start_time = time.time()
        
        elapsed = time.time() - self.welcome_start_time
        if elapsed > 5.0:
            self.current_step = "face_detection"
            print("🎬 Starting face detection...")
        
        return frame
    
    def handle_face_detection(self, frame):
        """Face detection with visual feedback"""
        face_detected = self.camera.detect_face(frame)
        
        if face_detected:
            face_coords = getattr(self.camera, 'face_coords', None)
            
            if face_coords:
                frame = self.ui.draw_face_outline(frame, face_coords)
            
            if self.face_detected_time == 0:
                self.face_detected_time = time.time()
            
            elapsed = time.time() - self.face_detected_time
            progress = min(elapsed / 2.0, 1.0)
            frame = self.ui.draw_detection_progress(frame, progress)
            
            if elapsed > 2.0:
                self.current_step = "background_selection"
                print("✅ Face detected! Moving to background selection...")
        else:
            self.face_detected_time = 0
            frame = self.ui.draw_face_detection_guide(frame)
        
        return frame
    
    def handle_background_selection(self, frame, finger_pos, is_clicking):
        """Background selection with MediaPipe segmentation"""
        # Apply selected background
        if self.selected_background is not None:
            frame = self.bg_engine.apply_background(frame, self.selected_background)
        
        # Draw selection UI
        frame = self.popup_manager.draw_background_popups(frame, self.backgrounds)
        
        # Hover effects
        if finger_pos:
            frame = self.popup_manager.highlight_popup_on_hover(frame, finger_pos)
            frame = self.draw_selection_progress(frame, finger_pos, (0, 255, 255))
        
        # Instruction
        cv2.putText(frame, "Select Background", (540, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Handle selection
        if is_clicking:
            selected_idx = self.popup_manager.check_popup_click(finger_pos)
            if selected_idx is not None and selected_idx < len(self.backgrounds):
                self.selected_background = self.backgrounds[selected_idx]
                self.bg_engine.change_background(self.selected_background)
                print(f"✅ Background selected: {os.path.basename(self.selected_background)}")
                self.current_step = "clothing_selection"
        
        return frame
    
    def handle_clothing_selection(self, frame, finger_pos, is_clicking):
        """Clothing selection - T-shirt (HSV) or Shirt (Overlay)"""
        
        # Apply background first
        if self.selected_background:
            frame = self.bg_engine.apply_background(frame, self.selected_background)
        
        # Apply clothing overlay
        if self.selected_clothing_type and self.selected_clothing_item is not None:
            if self.frame_count % self.process_clothing_every_n == 0:
                frame = self.clothing_engine.apply_clothing_item(
                    frame, self.selected_clothing_type, self.selected_clothing_item
                )
                self.last_clothing_frame = frame.copy()
            else:
                if self.last_clothing_frame is not None:
                    frame = self.last_clothing_frame.copy()
        
        # Multi-step selection
        if not hasattr(self, 'clothing_step'):
            self.clothing_step = "initial"
        
        # STEP 1: Choose category (T-shirt LEFT, Shirt RIGHT)
        if self.clothing_step == "initial":
            initial_options = ["tshirts", "shirts"]
            frame = self.popup_manager.draw_initial_clothing_choice(frame, initial_options)
            
            if finger_pos:
                frame = self.popup_manager.highlight_popup_on_hover(frame, finger_pos)
                frame = self.draw_selection_progress(frame, finger_pos, (0, 255, 255))
            
            cv2.putText(frame, "T-Shirt (LEFT - HSV Color) or Shirt (RIGHT - Image Overlay)", 
                       (240, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            
            if is_clicking:
                selected_idx = self.popup_manager.check_popup_click(finger_pos)
                if selected_idx is not None and selected_idx < len(initial_options):
                    self.selected_clothing_category = initial_options[selected_idx]
                    
                    if self.selected_clothing_category == "tshirts":
                        self.clothing_step = "tshirt_selection"
                        print("✅ T-shirt category selected - HSV Color Replacement")
                    elif self.selected_clothing_category == "shirts":
                        self.clothing_step = "shirt_selection"
                        print("✅ Shirt category selected - Image Overlay")
        
        # STEP 2A: T-shirt selection (HSV method)
        elif self.clothing_step == "tshirt_selection":
            available_tshirts = self.clothing_engine.get_available_clothing("tshirts")
            
            if available_tshirts:
                frame = self.popup_manager.draw_clothing_item_popups(frame, available_tshirts, "tshirts")
                
                if finger_pos:
                    frame = self.popup_manager.highlight_popup_on_hover(frame, finger_pos)
                    frame = self.draw_selection_progress(frame, finger_pos, (255, 0, 255))
                
                cv2.putText(frame, f"Select T-Shirt Color ({len(available_tshirts)} available) - HSV Replacement", 
                           (320, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
                
                if is_clicking:
                    selected_idx = self.popup_manager.check_popup_click(finger_pos)
                    if selected_idx is not None and selected_idx < len(available_tshirts):
                        self.selected_clothing_type = "tshirts"
                        self.selected_clothing_item = selected_idx
                        self.current_step = "complete"
                        print(f"✅ T-shirt {selected_idx + 1} selected - HSV COLOR REPLACEMENT!")
            else:
                cv2.putText(frame, "⚠️ No T-shirts found - Add images to assets/clothing/tshirts/", 
                           (280, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # STEP 2B: Shirt selection (Overlay method)
        elif self.clothing_step == "shirt_selection":
            available_shirts = self.clothing_engine.get_available_clothing("shirts")
            
            if available_shirts:
                frame = self.popup_manager.draw_clothing_item_popups(frame, available_shirts, "shirts")
                
                if finger_pos:
                    frame = self.popup_manager.highlight_popup_on_hover(frame, finger_pos)
                    frame = self.draw_selection_progress(frame, finger_pos, (255, 255, 0))
                
                cv2.putText(frame, f"Select Formal Shirt ({len(available_shirts)} available) - Image Overlay", 
                           (320, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
                
                if is_clicking:
                    selected_idx = self.popup_manager.check_popup_click(finger_pos)
                    if selected_idx is not None and selected_idx < len(available_shirts):
                        self.selected_clothing_type = "shirts"
                        self.selected_clothing_item = selected_idx
                        self.current_step = "complete"
                        print(f"✅ Shirt {selected_idx + 1} selected - IMAGE OVERLAY!")
            else:
                cv2.putText(frame, "⚠️ No shirts found - Add images to assets/clothing/shirts/", 
                           (280, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        return frame
    
    def handle_complete_screen(self, frame, finger_pos, is_clicking):
        """Completion screen with final result"""
        
        # Apply background
        if self.selected_background:
            frame = self.bg_engine.apply_background(frame, self.selected_background)
        
        # Apply clothing
        if self.selected_clothing_type and self.selected_clothing_item is not None:
            if self.frame_count % self.process_clothing_every_n == 0:
                frame = self.clothing_engine.apply_clothing_item(
                    frame, self.selected_clothing_type, self.selected_clothing_item
                )
                self.last_clothing_frame = frame.copy()
            else:
                if self.last_clothing_frame is not None:
                    frame = self.last_clothing_frame.copy()
        
        # Completion UI
        frame = self.ui.draw_completion_screen(frame)
        
        # Method indicator
        method = "HSV Color Replacement" if self.selected_clothing_type == "tshirts" else "Image Overlay"
        cv2.putText(frame, f"Method: {method}", (10, frame.shape[0] - 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"FPS: {self.current_fps}", (10, frame.shape[0] - 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Save on click
        if is_clicking and finger_pos:
            self.save_professional_result(frame)
        
        return frame
    
    def draw_selection_progress(self, frame, finger_pos, color):
        """Selection progress animation"""
        if hasattr(self.gesture_detector, 'hold_start_time') and self.gesture_detector.hold_start_time:
            hold_progress = ((time.time() - self.gesture_detector.hold_start_time) / 
                           self.gesture_detector.hold_threshold)
            hold_progress = min(hold_progress, 1.0)
            
            if hold_progress > 0:
                percentage = int(hold_progress * 100)
                x, y = finger_pos
                
                progress_radius = int(40 + 20 * hold_progress)
                final_color = color if hold_progress < 0.8 else (0, 255, 0)
                
                cv2.circle(frame, (x, y), progress_radius, final_color, 4)
                
                if hold_progress > 0.5:
                    inner_radius = int(progress_radius * (hold_progress - 0.5) * 2)
                    cv2.circle(frame, (x, y), inner_radius, final_color, -1)
                
                cv2.putText(frame, f"{percentage}%", (x + 50, y - 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, final_color, 3)
                
                if hold_progress > 0.9:
                    cv2.putText(frame, "SELECTED!", (x + 50, y + 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, final_color, 2)
        
        return frame
    
    def save_professional_result(self, frame):
        """Save professional result"""
        timestamp = int(time.time())
        method = "tshirt_hsv" if self.selected_clothing_type == "tshirts" else "shirt_overlay"
        filename = f"professional_makeover_{method}_{timestamp}.jpg"
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
        print(f"\n📸 RESULT SAVED: {filename}")
        
        # Show notification
        notification_frame = frame.copy()
        cv2.putText(notification_frame, "SAVED SUCCESSFULLY!", 
                   (frame.shape[1]//2 - 250, frame.shape[0]//2),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 0), 4)
        cv2.imshow('AI Professional Makeover', notification_frame)
        cv2.waitKey(1500)
    
    def capture_screenshot(self, frame):
        """Capture screenshot"""
        timestamp = int(time.time())
        filename = f"screenshot_{timestamp}.jpg"
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"📸 Screenshot saved: {filename}")
    
    def restart_application(self):
        """Restart application"""
        print("\n🔄 Restarting...")
        
        self.current_step = "welcome"
        self.face_detected_time = 0
        self.selected_background = None
        self.selected_clothing_type = None
        self.selected_clothing_item = None
        self.last_clothing_frame = None
        
        # Clear welcome timer
        if hasattr(self, 'welcome_start_time'):
            delattr(self, 'welcome_start_time')
        
        for attr in ['clothing_step', 'selected_clothing_category']:
            if hasattr(self, attr):
                delattr(self, attr)
        
        self.clothing_engine.reset_pose_history()
        self.clothing_engine.clear_cache()
        
        print("✅ Restarted successfully!")
    
    def cleanup(self):
        """Clean up resources"""
        print("\n👋 Shutting down...")
        self.camera.release()
        cv2.destroyAllWindows()
        print("✅ Application closed!")
        
        

if __name__ == "__main__":
    try:
        print("\n" + "="*70)
        print("🌟 AI PROFESSIONAL MAKEOVER 🌟")
        print("Hybrid System: T-shirt HSV + Shirt Overlay")
        print("="*70)
        print("\n✨ FEATURES:")
        print("   ✓ Face detection")
        print("   ✓ Background replacement (MediaPipe)")
        print("   ✓ T-shirts: HSV color replacement")
        print("   ✓ Shirts: Actual image overlay")
        print("   ✓ Gesture control")
        print("\n📝 WORKFLOW:")
        print("   1. Face detection (2 seconds)")
        print("   2. Select background (8 options)")
        print("   3. Choose: T-shirt (LEFT) or Shirt (RIGHT)")
        print("   4. Select specific item")
        print("   5. Save result!")
        print("\n💡 TIPS:")
        print("   • Good lighting is essential")
        print("   • Sit 60-90cm from camera")
        print("   • Face camera directly")
        print("   • Hold finger still to select (1.5 seconds)")
        print("="*70)
        print("\nStarting application...\n")
        
        app = ProfessionalMakeoverApp()
        app.run()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
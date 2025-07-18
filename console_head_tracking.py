# Console Head Tracking Application
# Main application controller for console-based head tracking
# by Daniel Sami Mitwalli

import time
from src.imu_data import IMUData
from src.head_tracker import HeadTracker
from src.imu_reader import IMUReader
from src.keyboard_handler import KeyboardHandler
from src.display_manager import DisplayManager

class ConsoleHeadTrackingApp:
    """Main application controller for console head tracking"""
    
    def __init__(self):
        self.head_tracker = HeadTracker()
        self.keyboard_handler = KeyboardHandler()
        self.display_manager = DisplayManager()
    
    def process_keyboard_input(self):
        """Process keyboard commands"""
        key = self.keyboard_handler.get_key()
        
        if key:
            try:
                if key == 't':
                    self.head_tracker.zero_view()
                    self.display_manager.show_message("🎯 VIEW ZEROED!", "Current orientation is now the reference point", 2)
                elif key == 'r':
                    self.head_tracker.reset_calibration()
                    self.display_manager.show_message("🔄 CALIBRATION RESET!", "Please recalibrate...", 1)
                elif key == 'q' or key == '\x03':
                    raise KeyboardInterrupt
                else:
                    self.display_manager.show_help()
            except Exception as e:
                print(f"Error processing key '{key}': {e}")
                time.sleep(1)
    
    def head_tracking_callback(self, imu_data: IMUData, message_count: int, rate: float) -> None:
        """Main callback for processing IMU data"""
        
        # Handle keyboard input during normal operation
        if self.head_tracker.is_calibrated:
            self.process_keyboard_input()
        
        # Handle calibration
        if not self.head_tracker.is_calibrated:
            self.head_tracker.calibrate_gyroscope(imu_data)
            
            if message_count % 50 == 0:
                self.display_manager.show_calibration_progress(self.head_tracker, imu_data)
            
            if self.head_tracker.is_calibrated:
                self.display_manager.show_calibration_complete(self.head_tracker)
            return
        
        # Normal operation - update and display
        self.head_tracker.update(imu_data)
        
        if message_count % 10 == 0:
            self.display_manager.show_head_tracking_display(self.head_tracker, imu_data, message_count, rate)
    
    def run(self):
        """Run the head tracking application"""
        self.display_manager.show_startup_instructions()
        
        self.keyboard_handler.start_keyboard_thread()
        input("Press ENTER when glasses are stable and ready...")
        
        print("\n💡 TIP: If T key doesn't work, try typing 't' and pressing ENTER")
        print("=" * 60)
        
        with IMUReader(callback=self.head_tracking_callback) as reader:
            reader.run()

def main():
    """Main function - Console Head Tracking"""
    app = ConsoleHeadTrackingApp()
    app.run()

def main_raw():
    """Alternative: Raw data output"""
    with IMUReader() as reader:
        reader.run()

if __name__ == "__main__":
    main()

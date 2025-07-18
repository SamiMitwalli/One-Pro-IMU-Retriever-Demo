# Display Manager
# Console display formatting and output for head tracking
# by Daniel Sami Mitwalli

import time
import sys
from src.head_tracker import HeadTracker
from src.imu_data import IMUData

class DisplayManager:
    """Handles all console display output for head tracking"""
    
    def clear_screen(self):
        """Clear the console screen"""
        print("\033[2J\033[H")
    
    def show_message(self, title: str, message: str, duration: int):
        """Show a temporary message"""
        self.clear_screen()
        print("=" * 60)
        print(title)
        print("=" * 60)
        print(message)
        print("=" * 60)
        time.sleep(duration)

    def show_help(self):
        """Show keyboard commands"""
        self.clear_screen()
        print("=" * 60)
        print("⌨️  KEYBOARD COMMANDS")
        print("=" * 60)
        print("T - Zero view (set current orientation as forward)")
        print("R - Recalibrate gyroscope")
        print("Q - Quit program")
        print("=" * 60)
        time.sleep(1.5)

    def show_calibration_progress(self, tracker: HeadTracker, imu_data: IMUData):
        """Show calibration progress"""
        progress = tracker.get_calibration_progress()
        self.clear_screen()
        print("=" * 60)
        print("           XREAL ONE PRO HEAD TRACKING")
        print("=" * 60)
        print("\n🔄 CALIBRATING GYROSCOPE...")
        print(f"Keep glasses STATIONARY for calibration")
        print(f"Progress: {progress:.1f}% ({tracker.calibration_count}/{tracker.calibration_target})")
        print(f"\nCurrent readings:")
        print(f"  Gx: {imu_data.gx:+6.2f}  Gy: {imu_data.gy:+6.2f}  Gz: {imu_data.gz:+6.2f}")
        print("=" * 60)

    def show_calibration_complete(self, tracker: HeadTracker):
        """Show calibration complete message"""
        self.clear_screen()
        print("=" * 60)
        print("✅ CALIBRATION COMPLETE!")
        print("=" * 60)
        print(f"Gyroscope bias values:")
        print(f"  Bias X: {tracker.gyro_bias_x:+6.2f}")
        print(f"  Bias Y: {tracker.gyro_bias_y:+6.2f}")
        print(f"  Bias Z: {tracker.gyro_bias_z:+6.2f}")
        print("\n🎯 Head tracking is now active!")
        print("Move your head around to test...")
        print("=" * 60)
        time.sleep(2)

    def show_head_tracking_display(self, tracker: HeadTracker, imu_data: IMUData, message_count: int, rate: float):
        """Show main head tracking display"""
        rel_orientation = tracker.get_relative_orientation()
        movement = tracker.get_movement_description(imu_data)
        
        pitch_bar = tracker.get_orientation_bar(rel_orientation['pitch'], 90.0)
        yaw_bar = tracker.get_orientation_bar(rel_orientation['yaw'], 90.0)
        roll_bar = tracker.get_orientation_bar(rel_orientation['roll'], 90.0)
        
        self.clear_screen()
        print("=" * 60)
        print("           XREAL ONE PRO HEAD TRACKING")
        print("=" * 60)
        print(f"Rate: {rate:.1f}Hz | Message: {message_count:06d}")
        print(f"Movement: {movement}")
        print()
        
        # Show zero view status
        zero_active = (tracker.zero_pitch != 0.0 or tracker.zero_yaw != 0.0 or tracker.zero_roll != 0.0)
        print("🎯 ZERO VIEW ACTIVE - Showing relative orientation" if zero_active else "📍 ABSOLUTE VIEW - Press 'T' to zero current view")
        print()
        
        print(f"PITCH (Up/Down):    {rel_orientation['pitch']:+6.1f}° {pitch_bar}")
        print(f"YAW (Left/Right):   {rel_orientation['yaw']:+6.1f}° {yaw_bar}")
        print(f"ROLL (Tilt):        {rel_orientation['roll']:+6.1f}° {roll_bar}")
        print()
        print("Raw Gyroscope:")
        print(f"  Gx: {imu_data.gx:+6.2f}  Gy: {imu_data.gy:+6.2f}  Gz: {imu_data.gz:+6.2f}")
        print()
        print("Calibrated Gyroscope:")
        print(f"  Gx: {imu_data.gx - tracker.gyro_bias_x:+6.2f}  Gy: {imu_data.gy - tracker.gyro_bias_y:+6.2f}  Gz: {imu_data.gz - tracker.gyro_bias_z:+6.2f}")
        print()
        print("Accelerometer:")
        print(f"  Ax: {imu_data.ax:+6.3f}  Ay: {imu_data.ay:+6.3f}  Az: {imu_data.az:+6.3f}")
        print()
        
        tty_status = "✅ TTY" if sys.stdin.isatty() else "❌ Non-TTY"
        print(f"Keyboard Status: {tty_status}")
        print("Press 'T' to zero view | Press 'R' to recalibrate | Press 'Q' or Ctrl+C to quit")
        print("💡 If uppercase key doesn't work, try typing lowercase and pressing ENTER")
    
    def show_startup_instructions(self):
        """Show startup instructions"""
        print("Starting XREAL One Pro Head Tracking...")
        print("=" * 60)
        print("📋 INSTRUCTIONS:")
        print("1. Place glasses on a FLAT, STABLE surface")
        print("2. Keep them COMPLETELY STILL during calibration")
        print("3. After calibration, put on glasses and move around!")
        print("4. Press 'T' to zero view, 'R' to recalibrate, 'Q' to quit")
        print("=" * 60)

# Head Tracking Logic
# Head orientation tracking with sensor fusion
# by Daniel Sami Mitwalli

import time
import math
from src.imu_data import IMUData

class HeadTracker:
    """Head tracking state manager with sensor fusion"""
    def __init__(self):
        # Calibration state
        self.gyro_bias_x = 0.0
        self.gyro_bias_y = 0.0
        self.gyro_bias_z = 0.0
        self.is_calibrated = False
        self.calibration_samples = []
        self.calibration_count = 0
        self.calibration_target = 500
        
        # Head orientation (degrees)
        self.pitch = 0.0  # Up/down (nodding)
        self.yaw = 0.0    # Left/right (head turns)
        self.roll = 0.0   # Tilting head
        
        # Zero-point reference
        self.zero_pitch = 0.0
        self.zero_yaw = 0.0
        self.zero_roll = 0.0
        
        # Timing and thresholds
        self.last_time = time.time()
        self.movement_threshold = 0.5  # degrees/second
        
        # Scaling factors for realistic head movement ranges
        self.pitch_scale = 3.0
        self.yaw_scale = 60.0
        self.roll_scale = 1.0
        
    def calibrate_gyroscope(self, imu_data: IMUData) -> bool:
        """Collect samples for gyroscope bias calibration"""
        if self.is_calibrated:
            return True
            
        self.calibration_samples.append([imu_data.gx, imu_data.gy, imu_data.gz])
        self.calibration_count += 1
        
        if self.calibration_count >= self.calibration_target:
            # Calculate average bias
            samples = self.calibration_samples
            self.gyro_bias_x = sum(s[0] for s in samples) / len(samples)
            self.gyro_bias_y = sum(s[1] for s in samples) / len(samples)
            self.gyro_bias_z = sum(s[2] for s in samples) / len(samples)
            
            self.is_calibrated = True
            self.pitch = self.yaw = self.roll = 0.0
            self.last_time = 0
            return True
        
        return False
    
    def reset_calibration(self):
        """Reset calibration state"""
        self.calibration_samples = []
        self.calibration_count = 0
        self.is_calibrated = False
        self.gyro_bias_x = self.gyro_bias_y = self.gyro_bias_z = 0.0
        
    def zero_view(self):
        """Set current orientation as the new zero reference point"""
        self.zero_pitch = self.pitch
        self.zero_yaw = self.yaw
        self.zero_roll = self.roll
        
    def get_relative_orientation(self):
        """Get orientation relative to the zero reference point"""
        return {
            'pitch': self._wrap_angle((self.pitch - self.zero_pitch) * self.pitch_scale),
            'yaw': self._wrap_angle((self.yaw - self.zero_yaw) * self.yaw_scale),
            'roll': self._wrap_angle((self.roll - self.zero_roll) * self.roll_scale)
        }
        
    def get_calibration_progress(self) -> float:
        """Get calibration progress as percentage"""
        return (self.calibration_count / self.calibration_target) * 100
        
    def update(self, imu_data: IMUData) -> None:
        """Update head orientation using sensor fusion"""
        if not self.is_calibrated:
            return
            
        current_time = time.time()
        dt = current_time - self.last_time
        
        if self.last_time == 0:
            self.last_time = current_time
            return
        
        # Remove gyroscope bias
        gyro_x = imu_data.gx - self.gyro_bias_x
        gyro_y = imu_data.gy - self.gyro_bias_y
        gyro_z = imu_data.gz - self.gyro_bias_z
        
        # Gyroscope integration (short-term accurate)
        pitch_gyro = self.pitch + gyro_x * dt
        yaw_gyro = self.yaw + gyro_y * dt
        roll_gyro = self.roll + gyro_z * dt
        
        # Accelerometer orientation (long-term stable)
        ax, ay, az = imu_data.ax, imu_data.ay, imu_data.az
        acc_magnitude = math.sqrt(ax*ax + ay*ay + az*az)
        
        if acc_magnitude > 0.01:
            pitch_accel = math.atan2(-ax, math.sqrt(ay*ay + az*az)) * 180 / math.pi
            roll_accel = math.atan2(ay, az) * 180 / math.pi
            
            # Complementary filter (sensor fusion)
            alpha = 0.96
            self.pitch = alpha * pitch_gyro + (1 - alpha) * pitch_accel
            self.yaw = yaw_gyro  # Only gyroscope for yaw
            self.roll = alpha * roll_gyro + (1 - alpha) * roll_accel
        else:
            # Fallback to gyroscope-only
            self.pitch = pitch_gyro
            self.yaw = yaw_gyro
            self.roll = roll_gyro
        
        # Wrap angles to ±180°
        self.pitch = self._wrap_angle(self.pitch)
        self.yaw = self._wrap_angle(self.yaw)
        self.roll = self._wrap_angle(self.roll)
        
        self.last_time = current_time
    
    def _wrap_angle(self, angle: float) -> float:
        """Keep angle between -180 and 180 degrees"""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle
    
    def get_movement_description(self, imu_data: IMUData) -> str:
        """Get human-readable description of head movement"""
        gyro_x = imu_data.gx - self.gyro_bias_x
        gyro_y = imu_data.gy - self.gyro_bias_y
        gyro_z = imu_data.gz - self.gyro_bias_z
        
        movements = []
        if abs(gyro_x) > self.movement_threshold:
            movements.append("NODDING UP" if gyro_x > 0 else "NODDING DOWN")
        if abs(gyro_y) > self.movement_threshold:
            movements.append("TURNING RIGHT" if gyro_y > 0 else "TURNING LEFT")
        if abs(gyro_z) > self.movement_threshold:
            movements.append("TILTING RIGHT" if gyro_z > 0 else "TILTING LEFT")
        
        return " + ".join(movements) if movements else "STATIONARY"
    
    def get_orientation_bar(self, value: float, max_val: float = 45.0) -> str:
        """Create a visual bar representation of orientation"""
        normalized = max(-1, min(1, value / max_val))
        bar_length = 20
        center = bar_length // 2
        pos = int(center + normalized * (center - 1))
        
        bar = ['-'] * bar_length
        bar[center] = '|'  # Center line
        bar[pos] = '●'     # Current position
        
        return ''.join(bar)

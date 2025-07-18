# IMU Data Structures
# Core data classes for IMU sensor data
# by Daniel Sami Mitwalli

from dataclasses import dataclass

@dataclass
class IMUData:
    """IMU sensor data structure"""
    gx: float  # Gyroscope X (pitch rate)
    gy: float  # Gyroscope Y (yaw rate)  
    gz: float  # Gyroscope Z (roll rate)
    ax: float  # Accelerometer X
    ay: float  # Accelerometer Y
    az: float  # Accelerometer Z
    
    def __str__(self):
        return (f"Gx={self.gx:.3f}, Gy={self.gy:.3f}, Gz={self.gz:.3f} | "
                f"Ax={self.ax:.3f}, Ay={self.ay:.3f}, Az={self.az:.3f}")

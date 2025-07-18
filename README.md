# One Pro IMU Retriever Demo

A demo head tracking solution for the `XREAL One Pro` glasses using IMU sensor data.

This is a proof of concept. The `imu_reader.py` retrieves a stream of data from the XREAL One Pro's IMU via TCP, parsing the gyroscope and accelerometer data. I hope this will be helpful for future open-source projects involving the XReal One/One Pro, such as those involving support for e.g. SteamVR and Android XR.

## 🚀 Quick Start

### Option 1: Use the Launcher (Recommended)
```bash
python launcher.py
```

### Option 2: Direct Launch Demo

```bash
# Console mode
python console_head_tracking.py

# 3D visualization mode
python head_tracking_3d.py
```

## 📋 Requirements

### Basic Console Mode
- Python 3.7+
- XREAL One Pro glasses

### 3D Visualization Mode
Additional requirements:
```bash
pip install pygame PyOpenGL PyOpenGL_accelerate numpy
```

## 🎮 Features

### Console Mode
- **Real-time head tracking** with pitch, yaw, roll values
- **Visual orientation bars** showing head position
- **Automatic gyroscope calibration** (press R to set recalibrate bias)
- **Zero view functionality** (press T to set current orientation as forward)
- **Movement descriptions** (nodding, turning, tilting)

### 3D Visualization Mode
- **OpenGL-based 3D cube** controlled by head movement

## ⌨️ Controls

### Console Mode
- **T** - Zero view (set current orientation as forward)
- **R** - Recalibrate gyroscope
- **Q** - Quit
- **Ctrl+C** - Emergency quit

### 3D Mode
- **T** - Zero view
- **R** - Recalibrate gyroscope
- **+/=** - Increase sensitivity
- **-** - Decrease sensitivity
- **Q/ESC** - Quit

## 🔧 Configuration

### Scaling Factors (in fetchX1imu.py)
```python
# Adjust these values in HeadTracker.__init__()
self.pitch_scale = 3.0   # Up/down sensitivity
self.yaw_scale = 60.0    # Left/right sensitivity  
self.roll_scale = 1.0    # Tilt sensitivity
```

## 🛠️ Technical Details

### IMU Data Processing
1. **TCP Connection** to glasses at 169.254.2.1:52998
2. **Protocol Decoding** of binary sensor data
3. **Gyroscope Calibration** (500 samples at startup)
4. **Sensor Fusion** using complementary filter (96% gyro, 4% accelerometer)
5. **Orientation Integration** with bias correction

### Coordinate System
- **X-axis (Pitch)**: Forward/backward head tilt
- **Y-axis (Yaw)**: Left/right head rotation
- **Z-axis (Roll)**: Left/right head tilt

## 🐛 Troubleshooting

### Connection Issues
- I tested it only on XReal One Pro, maybe the One is not supported.
- Check network connection to 169.254.2.1
- Verify glasses haven't ethernet turned off (developer menu).

### Calibration Problems
- Keep glasses completely stationary during calibration
- Place on flat surface for best results
- Press R to recalibrate if tracking drifts

### 3D Mode Issues
- Install all required packages: `pip install pygame PyOpenGL PyOpenGL_accelerate numpy`
- Ensure OpenGL drivers are properly installed
- On macOS, may need to grant Python screen recording permissions

### T, R or Q Key Not Working
- Try typing 't', 'r' or 'q' and pressing ENTER instead of just T, R or Q
- Check if terminal is in focus
- Use launcher for better keyboard handling

## Nice to Know

- **Update Rate**: ~1000Hz from IMU sensor
- **Display Rate**: 60Hz (3D mode), 10Hz (console mode)
- **Latency**: <10ms end-to-end
- **Calibration Time**: ~0.5 seconds

By Daniel Sami Mitwalli
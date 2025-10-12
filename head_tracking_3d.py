# 3D Head Tracking Visualization
# VR-style head tracking for One Pro IMU data
# by Daniel Sami Mitwalli

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import threading
import time
import numpy as np

from src.head_tracker import HeadTracker
from src.imu_data import IMUData
from src.imu_reader import IMUReader

def compute_fov(diagonal_in, aspect_ratio, viewer_distance_m):
    in_to_m = 0.0254
    diagonal_m = diagonal_in * in_to_m

    # Calculate screen height and width
    h = diagonal_m / math.sqrt(1 + aspect_ratio**2)
    w = h * aspect_ratio

    # Compute vertical FOV
    fov_y = 2 * math.degrees(math.atan((h / 2) / viewer_distance_m))

    return fov_y, w, h


# Initialize pygame and OpenGL
def init_demo():
    pygame.init()
    display = (1920, 1080)
    diagonal_in = 162
    aspect_ratio = 16 / 9
    viewer_distance_m = 4.0

    pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption("Demo Head Tracking")
    
    # OpenGL settings
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    glClearColor(0.1, 0.1, 0.1, 1.0)  # Dark gray background
    glShadeModel(GL_SMOOTH)
    
    # Set up perspective
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    fov_y, _, _ = compute_fov(diagonal_in, aspect_ratio, viewer_distance_m)

    # Use in OpenGL
    gluPerspective(fov_y, aspect_ratio, 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    print("OpenGL initialized successfully!")
    return display

def draw_cube():
    """Draw a colored cube with wireframe"""
    vertices = [
        [1, 1, -1], [1, -1, -1], [-1, -1, -1], [-1, 1, -1],    # Back face
        [1, 1, 1], [1, -1, 1], [-1, -1, 1], [-1, 1, 1]         # Front face
    ]
    
    faces = [
        [0, 1, 2, 3],  # Back
        [4, 7, 6, 5],  # Front
        [0, 4, 5, 1],  # Right
        [2, 6, 7, 3],  # Left
        [0, 3, 7, 4],  # Top
        [1, 5, 6, 2]   # Bottom
    ]
    
    colors = [
        [0.8, 0.2, 0.2], [0.2, 0.8, 0.2], [0.2, 0.2, 0.8],
        [0.8, 0.8, 0.2], [0.8, 0.2, 0.8], [0.2, 0.8, 0.8]
    ]
    
    # Draw filled faces
    glBegin(GL_QUADS)
    for i, face in enumerate(faces):
        glColor3fv(colors[i])
        for vertex in face:
            glVertex3fv(vertices[vertex])
    glEnd()
    
    # Draw wireframe
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2)
    glBegin(GL_LINES)
    # Back face
    glVertex3fv(vertices[0]); glVertex3fv(vertices[1])
    glVertex3fv(vertices[1]); glVertex3fv(vertices[2])
    glVertex3fv(vertices[2]); glVertex3fv(vertices[3])
    glVertex3fv(vertices[3]); glVertex3fv(vertices[0])
    # Front face
    glVertex3fv(vertices[4]); glVertex3fv(vertices[5])
    glVertex3fv(vertices[5]); glVertex3fv(vertices[6])
    glVertex3fv(vertices[6]); glVertex3fv(vertices[7])
    glVertex3fv(vertices[7]); glVertex3fv(vertices[4])
    # Connecting edges
    glVertex3fv(vertices[0]); glVertex3fv(vertices[4])
    glVertex3fv(vertices[1]); glVertex3fv(vertices[5])
    glVertex3fv(vertices[2]); glVertex3fv(vertices[6])
    glVertex3fv(vertices[3]); glVertex3fv(vertices[7])
    glEnd()

def draw_axis():
    """Draw coordinate axes"""
    glLineWidth(4)
    glBegin(GL_LINES)
    # X axis - Red
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(0, 0, 0); glVertex3f(3, 0, 0)
    # Y axis - Green
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0, 0, 0); glVertex3f(0, 3, 0)
    # Z axis - Blue
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0, 0, 0); glVertex3f(0, 0, 3)
    glEnd()
    glLineWidth(1)


class HeadTracking3D:
    def __init__(self):
        self.head_tracker = HeadTracker()
        self.pitch = 0.0
        self.yaw = 0.0
        self.roll = 0.0
        self.running = True
        self.imu_thread = None
        self.camera_sensitivity = 1.0
        self.debug_mode = True
        
    def imu_callback(self, imu_data: IMUData, message_count: int, rate: float):
        """Callback for IMU data"""
        if not self.head_tracker.is_calibrated:
            self.head_tracker.calibrate_gyroscope(imu_data)
            if self.debug_mode and message_count % 100 == 0:
                progress = self.head_tracker.get_calibration_progress()
                print(f"Calibration progress: {progress:.1f}%")
            return
            
        # Update head tracking
        self.head_tracker.update(imu_data)
        rel_orientation = self.head_tracker.get_relative_orientation()
        
        # Update camera angles
        self.pitch = math.radians(rel_orientation['pitch']) * self.camera_sensitivity
        self.yaw = math.radians(rel_orientation['yaw']) * self.camera_sensitivity
        self.roll = math.radians(rel_orientation['roll']) * self.camera_sensitivity
        
        # Debug output
        if self.debug_mode and message_count % 100 == 0:
            print(f"Pitch: {math.degrees(self.pitch):+6.1f}° "
                  f"Yaw: {math.degrees(self.yaw):+6.1f}° "
                  f"Roll: {math.degrees(self.roll):+6.1f}°")
    
    def start_imu_thread(self):
        """Start IMU data collection in a separate thread"""
        def imu_worker():
            try:
                with IMUReader(callback=self.imu_callback) as reader:
                    reader.run()
            except Exception as e:
                print(f"IMU Error: {e}")
        
        self.imu_thread = threading.Thread(target=imu_worker, daemon=True)
        self.imu_thread.start()
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    self.running = False
                elif event.key == pygame.K_t:
                    # Zero view
                    self.head_tracker.zero_view()
                    print("View zeroed!")
                elif event.key == pygame.K_r:
                    # Reset calibration
                    self.head_tracker.reset_calibration()
                    print("Calibration reset!")
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    # Increase sensitivity
                    self.camera_sensitivity = min(2.0, self.camera_sensitivity + 0.1)
                    print(f"Sensitivity: {self.camera_sensitivity:.1f}")
                elif event.key == pygame.K_MINUS:
                    # Decrease sensitivity
                    self.camera_sensitivity = max(0.1, self.camera_sensitivity - 0.1)
                    print(f"Sensitivity: {self.camera_sensitivity:.1f}")
    
    def render(self, viewport_x, eye_offset):
        """Render the 3D scene"""
        glViewport(viewport_x, 0, self.display[0] // 2, self.display[1])
        glLoadIdentity()
        
        if not self.head_tracker.is_calibrated:
            # Default view during calibration
            gluLookAt(0, 0, 8, 0, 0, 0, 0, 1, 0)
            draw_axis()
            glPushMatrix()
            draw_cube()
            glPopMatrix()
            
            if self.debug_mode:
                progress = self.head_tracker.get_calibration_progress()
                print(f"\rCalibration: {progress:.1f}%", end="", flush=True)
        else:
            
            # --- Inputs ---
            camera_x, camera_y, camera_z = 0, 0, 8  # Head position (fixed in your example)

            # === Look direction (from yaw/pitch) ===
            look_x = math.sin(self.yaw) * math.cos(self.pitch)
            look_y = -math.sin(self.pitch)
            look_z = -math.cos(self.yaw) * math.cos(self.pitch)
            look_dir = np.array([look_x, look_y, look_z], dtype=np.float32)
            look_dir /= np.linalg.norm(look_dir)

            # === Up vector (from pitch/roll/yaw) ===
            up_x = -math.sin(self.roll) * math.cos(self.yaw) - math.cos(self.roll) * math.sin(self.yaw) * (-math.sin(self.pitch))
            up_y = math.cos(self.roll) * math.cos(self.pitch)
            up_z = -math.sin(self.roll) * math.sin(self.yaw) + math.cos(self.roll) * math.cos(self.yaw) * (-math.sin(self.pitch))
            up_dir = np.array([up_x, up_y, up_z], dtype=np.float32)
            up_dir /= np.linalg.norm(up_dir)

            # === Right vector (needed for stereo offset) ===
            right_dir = np.cross(look_dir, up_dir)
            right_dir /= np.linalg.norm(right_dir)

            # === Apply eye offset to camera position and look-at target ===
            eye_shift = right_dir * eye_offset

            eye_pos = np.array([camera_x, camera_y, camera_z], dtype=np.float32) + eye_shift
            target_pos = eye_pos + look_dir  # Look in direction of view

            # === Set camera ===
            gluLookAt(
                eye_pos[0], eye_pos[1], eye_pos[2],      # Eye (camera) position
                target_pos[0], target_pos[1], target_pos[2],  # Target position
                up_dir[0], up_dir[1], up_dir[2]          # Up vector
            )
            
            # Draw scene objects (all static in world space)
            draw_axis()
            
            # Main cube at origin
            glPushMatrix()
            draw_cube()
            glPopMatrix()
            
            # Reference cubes
            positions = [(5, 0, 0), (-5, 0, 0), (0, 5, 0), (0, -5, 0)]
            for pos in positions:
                glPushMatrix()
                glTranslatef(*pos)
                glScalef(0.5, 0.5, 0.5)
                draw_cube()
                glPopMatrix()
            
            # Depth reference objects
            depth_positions = [(0, 0, 5), (0, 0, -5), (3, 3, 3), (-3, -3, -3)]
            scales = [0.3, 0.3, 0.2, 0.2]
            for pos, scale in zip(depth_positions, scales):
                glPushMatrix()
                glTranslatef(*pos)
                glScalef(scale, scale, scale)
                draw_cube()
                glPopMatrix()
            
            # 360° objects behind camera
            back_positions = [(0, 0, 15), (8, 0, 10), (-8, 0, 10)]
            back_scales = [0.4, 0.25, 0.25]
            for pos, scale in zip(back_positions, back_scales):
                glPushMatrix()
                glTranslatef(*pos)
                glScalef(scale, scale, scale)
                draw_cube()
                glPopMatrix()
        
    
    def run(self):
        """Main application loop"""
        print("Starting Head Tracking...")
        print("=" * 60)
        print("📋 CONTROLS:")
        print("• Move your head to control the camera")
        print("• T - Zero view (set current orientation as forward)")
        print("• R - Recalibrate gyroscope")
        print("• +/- - Increase/decrease sensitivity")
        print("• Q/ESC - Quit")
        print("=" * 60)
        
        self.display = init_demo()
        self.start_imu_thread()
        
        # Calibration phase
        print("🔄 Calibrating... Keep glasses stationary!")
        while not self.head_tracker.is_calibrated and self.running:
            self.handle_events()
            time.sleep(0.1)
        
        if self.head_tracker.is_calibrated:
            print("✅ Calibration complete! Put on glasses and move around.")

        # Main render loop
        clock = pygame.time.Clock()
        auto_zero_frames = 0
        while self.running:
            # Intial auto-zero view
            if auto_zero_frames == 3:
                self.head_tracker.zero_view()
                print("🎯 View auto-zeroed! Press 'T' to re-zero anytime.")
            if auto_zero_frames < 4:
                auto_zero_frames += 1
            
            self.handle_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            eye_offset = 0.05
            self.render(0, -eye_offset)
            self.render(self.display[0] // 2, eye_offset)
            pygame.display.flip()
            clock.tick(60)
            
            if self.head_tracker.is_calibrated:
                pygame.display.set_caption(
                    f"Head Tracking - "
                    f"Pitch: {math.degrees(self.pitch):+5.1f}° "
                    f"Yaw: {math.degrees(self.yaw):+5.1f}° "
                    f"Roll: {math.degrees(self.roll):+5.1f}° "
                    f"Sens: {self.camera_sensitivity:.1f}"
                )
        pygame.quit()

def main():
    """Main function"""
    try:
        app = HeadTracking3D()
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

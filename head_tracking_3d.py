# 3D Head Tracking Visualization
# VR-style head tracking for XREAL One Pro IMU data
# by Daniel Sami Mitwalli

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import threading
import time

from src.head_tracker import HeadTracker
from src.imu_data import IMUData
from src.imu_reader import IMUReader

# Initialize pygame and OpenGL
def init_demo():
    pygame.init()
    display = (800, 600)
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
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    print("OpenGL initialized successfully!")

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
    
    def render(self):
        """Render the 3D scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
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
            # VR-style head tracking: Fixed camera position, only viewing direction changes
            camera_x, camera_y, camera_z = 0, 0, 8
            
            # Calculate look direction from head tracking
            look_x = math.sin(self.yaw) * math.cos(self.pitch)
            look_y = -math.sin(self.pitch)
            look_z = -math.cos(self.yaw) * math.cos(self.pitch)
            
            # Calculate up vector with roll
            up_x = -math.sin(self.roll) * math.cos(self.yaw) - math.cos(self.roll) * math.sin(self.yaw) * (-math.sin(self.pitch))
            up_y = math.cos(self.roll) * math.cos(self.pitch)
            up_z = -math.sin(self.roll) * math.sin(self.yaw) + math.cos(self.roll) * math.cos(self.yaw) * (-math.sin(self.pitch))
            
            # Set camera view
            gluLookAt(camera_x, camera_y, camera_z,
                      camera_x + look_x, camera_y + look_y, camera_z + look_z,
                      up_x, up_y, up_z)
            
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
        
        pygame.display.flip()
    
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
        
        init_demo()
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
            self.render()
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

# Keyboard Input Handler
# Cross-platform keyboard input handling for head tracking
# by Daniel Sami Mitwalli

import sys
import select
import termios
import tty
import threading
import queue
import time

class KeyboardHandler:
    """Handles keyboard input for head tracking controls"""
    
    def __init__(self):
        self.keyboard_queue = queue.Queue()
        self.keyboard_thread = None
    
    def keyboard_input_thread(self):
        """Thread to handle keyboard input"""
        while True:
            try:
                if sys.stdin.isatty():
                    # Use normal input for TTY
                    char = input()
                    if char:
                        self.keyboard_queue.put(char[0].lower())
                else:
                    # Fallback for non-TTY environments
                    time.sleep(0.1)
            except (EOFError, KeyboardInterrupt):
                break
            except Exception:
                time.sleep(0.1)

    def start_keyboard_thread(self):
        """Start the keyboard input thread"""
        if self.keyboard_thread is None or not self.keyboard_thread.is_alive():
            self.keyboard_thread = threading.Thread(target=self.keyboard_input_thread, daemon=True)
            self.keyboard_thread.start()

    def get_keyboard_input(self):
        """Get keyboard input from queue"""
        try:
            return self.keyboard_queue.get_nowait()
        except queue.Empty:
            return None

    def kbhit(self):
        """Check if keyboard input is available"""
        try:
            if not sys.stdin.isatty():
                return False
            return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
        except:
            return False

    def getch(self):
        """Get a single character from stdin"""
        try:
            if not sys.stdin.isatty():
                return ""
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
        except:
            return ""
    
    def get_key(self):
        """Get a key press using multiple methods"""
        key = None
        
        # Try direct keyboard input
        try:
            if self.kbhit():
                key = self.getch().lower()
        except:
            pass
        
        # Try threaded keyboard input
        if not key:
            try:
                key = self.get_keyboard_input()
            except:
                pass
        
        return key

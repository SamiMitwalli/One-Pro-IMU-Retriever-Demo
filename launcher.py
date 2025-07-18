#!/usr/bin/env python3
# Head Tracking Launcher
# by Daniel Sami Mitwalli

import sys

def show_menu():
    print("=" * 60)
    print("         HEAD TRACKING DEMO")
    print("=" * 60)
    print("\nChoose your tracking mode:\n")
    print("1. Console Mode - Terminal-based head tracking")
    print("   • Shows pitch, yaw, roll values in terminal")
    print("   • Visual orientation bars")
    print("   • Keyboard controls (T/R/Q)\n")
    print("2. 3D Mode - OpenGL visualization")
    print("   • Real-time 3D cube controlled by head movement")
    print("   • Smooth camera control")
    print("   • Sensitivity adjustment\n")
    print("3. Exit\n")
    print("=" * 60)

def main():
    while True:
        show_menu()
        try:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                print("\n🎯 Starting Console Mode...")
                print("=" * 60)
                import console_head_tracking
                console_head_tracking.main()
                break
                
            elif choice == '2':
                print("\n🎮 Starting 3D Mode...")
                print("=" * 60)
                try:
                    import head_tracking_3d
                    head_tracking_3d.main()
                except ImportError as e:
                    print("❌ Error: Missing dependencies for 3D mode.")
                    print("Please install: pip install pygame PyOpenGL PyOpenGL_accelerate")
                    print(f"Details: {e}")
                    input("\nPress ENTER to continue...")
                    continue
                break
                
            elif choice == '3':
                print("\n👋 Goodbye!")
                sys.exit(0)
                
            else:
                print(f"\n❌ Invalid choice '{choice}'. Please enter 1, 2, or 3.")
                input("Press ENTER to continue...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press ENTER to continue...")

if __name__ == "__main__":
    main()

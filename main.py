import time
import sys
from game_control import join_game, align_camera, leave_game, reset_character
from detector import ChimeDetector

def main():
    print("=== Bee Swarm Simulator Wind Chime Detector ===")
    print("1. Join Game and Align Camera")
    print("2. Calibrate Chime Detection Region")
    print("3. Check Chimes (Requires Calibration)")
    print("4. Full Auto (Join -> Align -> Detect)")
    print("5. Align Camera Only")
    print("6. Exit")

    choice = input("Select an option: ")

    if choice == '1':
        join_game()
        align_camera()
    elif choice == '2':
        detector = ChimeDetector()
        print("Please make sure Roblox is open and the chimes are visible on screen.")
        time.sleep(2)
        detector.calibrate()
    elif choice == '3':
        detector = ChimeDetector()
        if not detector.roi:
            print("You must calibrate first. Choose option 2.")
        else:
            detector.detect_movement()
    elif choice == '4':
        detector = ChimeDetector()
        if not detector.roi:
            print("Notice: You haven't calibrated the chime region yet.")
            try:
                # We prompt them to calibrate initially
                print("Please make sure Roblox is open for calibration.")
                time.sleep(2)
                detector.calibrate()
            except Exception as e:
                print(f"Calibration failed: {e}")
                return

        while True:
            join_game()
            max_retries = 3
            found_movement = False
            
            for attempt in range(max_retries):
                align_camera()
                
                # Detect movement 
                result = detector.detect_movement(duration=3)
                
                if result is True:
                    print("========================================")
                    print("wind chimes are moving! stop auto mode.")
                    print("========================================")
                    found_movement = True
                    break
                elif result == "obstructed":
                    print("obstruction detected. rejoining a new server...")
                    break
                elif result == "missing":
                    print(f"Chimes missing (Attempt {attempt+1}/{max_retries}). Resetting character...")
                    if attempt < max_retries - 1:
                        reset_character()
                    else:
                        print("max reset retries reached for this server.")
                else:
                    print("chimes are static.")
                    break

            if found_movement:
                break

            print("Rejoining a new server...")
            leave_game()
            time.sleep(5)
    elif choice == '5':
        align_camera()
    elif choice == '6':
        sys.exit(0)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    try:
        while True:
            main()
            print()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

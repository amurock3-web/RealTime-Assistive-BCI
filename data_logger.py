import serial
import time
import csv
import os

# --- CONFIGURATION ---
ARDUINO_PORT = 'COM3'  
BAUD_RATE = 115200
DATA_DIR = 'dataset'


if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# The exact timeline of actions
TIMELINE = [
    (0,  "==== RELAX YOUR FACE ===="),
    (5,  "==== [ CLENCH JAW ] ===="),
    (8,  "==== RELAX ===="),
    (11, "==== [ CLENCH JAW ] ===="),
    (14, "==== RELAX ===="),
    (17, "==== [ WINK LEFT EYE ] ===="),
    (20, "==== RELAX ===="),
    (23, "==== [ WINK LEFT EYE ] ===="),
    (26, "==== RELAX ===="),
    (29, "==== [ WINK RIGHT EYE ] ===="),
    (32, "==== RELAX ===="),
    (35, "==== [ WINK RIGHT EYE ] ===="),
    (38, "==== RELAX ===="),
    (41, "==== [ DOUBLE BLINK ] ===="),
    (44, "==== RELAX ===="),
    (47, "==== [ DOUBLE BLINK ] ===="),
    (50, "==== RELAX UNTIL FINISHED ===="),
    (55, "==== STOP ====")
]

def main():
    print("========================================")
    print("   BCI CLINICAL DATA COLLECTION TOOL    ")
    print("========================================\n")
    
    subject_id = input("Enter Subject Name (e.g., pralhad): ").strip().lower()
    trial_num = input("Enter Trial Number (e.g., 01): ").strip()
    
    # --- ADDED TIMESTAMP LOGIC ---
    # This formats the current time as YearMonthDay_HourMinute (e.g., 20260428_1254)
    timestamp = time.strftime('%Y%m%d_%H%M')
    filename = f"{DATA_DIR}/{subject_id}_Trial{trial_num}_{timestamp}.csv"
    
    try:
        # If this fails, the Arduino IDE is probably open!
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE)
        time.sleep(2) 
        print(f"\nRecording to: {filename}\nStarting in 3 seconds...")
        time.sleep(3)
        
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Channel_1_Left', 'Channel_2_Right', 'Action'])
            
            start_time = time.time()
            current_idx = 0
            
            while current_idx < len(TIMELINE):
                elapsed = time.time() - start_time
                if elapsed >= TIMELINE[current_idx][0]:
                    label = TIMELINE[current_idx][1]
                    print(f"\n>>> {label} <<<")
                    current_idx += 1
                    if label == "==== STOP ====": break

                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if "," in line:
                        try:
                            ch1, ch2 = line.split(",")
                            writer.writerow([round(elapsed, 3), ch1, ch2, label])
                        except ValueError: pass
        print(f"\nSUCCESS! Data saved to {filename}")
    except PermissionError:
        print("\n[ERROR] ACCESS DENIED TO COM3!")
        print("Please close the Arduino IDE Serial Monitor and try again.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
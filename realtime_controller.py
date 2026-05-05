import serial
import time

# --- CONFIGURATION ---
ARDUINO_PORT = 'COM3'  # Change to your port!
BAUD_RATE = 115200

# The Magic Numbers we found from your graph
BASELINE = 500
THRESHOLD = 250 

def is_active(value):
    """Returns True if the signal spikes 250 points above or below baseline."""
    return abs(value - BASELINE) > THRESHOLD

def main():
    print(f"Connecting to Arduino on {ARDUINO_PORT}...")
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE)
        time.sleep(2)
        print("Connected! BCI Engine Active.")
        print("Waiting for facial commands...\n")
        
        # State Machine Variables
        is_moving = False
        last_both_spike_time = 0
        cooldown_time = 0
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if "," in line:
                    try:
                        ch1, ch2 = map(int, line.split(","))
                        current_time = time.time()
                        
                        # Only process commands if we aren't in a 1-second cooldown 
                        # (This prevents a single wink from triggering 10 times in a row)
                        if current_time > cooldown_time:
                            
                            ch1_spiked = is_active(ch1)
                            ch2_spiked = is_active(ch2)
                            
                            # --- LOGIC 1: LEFT WINK ---
                            if ch1_spiked and not ch2_spiked:
                                print(">>> COMMAND: TURN LEFT <<<")
                                cooldown_time = current_time + 1.0 # 1 second cooldown
                                
                            # --- LOGIC 2: RIGHT WINK ---
                            elif ch2_spiked and not ch1_spiked:
                                print(">>> COMMAND: TURN RIGHT <<<")
                                cooldown_time = current_time + 1.0
                                
                            # --- LOGIC 3: BOTH CHANNELS SPIKED (Jaw Clench or Blink) ---
                            elif ch1_spiked and ch2_spiked:
                                
                                # Check if this is the SECOND spike within 1.5 seconds (Double Blink)
                                if (current_time - last_both_spike_time) < 1.5:
                                    print("\n[!] DOUBLE BLINK DETECTED -> EMERGENCY STOP [!]\n")
                                    is_moving = False
                                    cooldown_time = current_time + 1.5 # Longer cooldown after stopping
                                    last_both_spike_time = 0 # Reset timer
                                    
                                # If it's just a single simultaneous spike (Jaw Clench)
                                else:
                                    is_moving = True
                                    print("\n[!] JAW CLENCH DETECTED -> TOGGLE FORWARD [!]\n")
                                    last_both_spike_time = current_time
                                    cooldown_time = current_time + 0.8
                                    
                    except ValueError:
                        pass # Ignore garbled data
                        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Arduino is plugged in and the IDE Serial Monitor is CLOSED.")

if __name__ == '__main__':
    main()
import pygame
import serial
import joblib
import numpy as np
from collections import deque
import time
import os

# ==========================================
# CONFIGURATION & HYPERPARAMETERS
# ==========================================
ARDUINO_PORT = 'COM3'  
BAUD_RATE = 115200
WINDOW_SIZE = 30       

# --- NEW: NOISE REJECTION BUFFER ---
ACTION_BUFFER_SIZE = 15  # Looks at the last 0.25 seconds of AI thoughts
CONFIDENCE_THRESHOLD = 0.55  

WINK_BOOST = 2.0  
BLINK_BOOST = 1.8
CLENCH_BOOST = 1.0 

MAX_SPEED = 1.5      
TURN_SPEED = 2.5     

# ==========================================
# FEATURE EXTRACTION 
# ==========================================
def extract_live_features(buffer):
    data = np.array(buffer)
    ch1, ch2 = data[:, 0], data[:, 1]

    def get_stats(ch):
        return [
            np.sqrt(np.mean(ch**2)),        
            np.mean(np.abs(np.diff(ch))),   
            np.var(ch),                     
            np.max(ch) - np.min(ch),        
            np.std(ch),                     
            ((ch[:-1] * ch[1:]) < 0).sum()  
        ]

    f1 = get_stats(ch1)
    f2 = get_stats(ch2)
    diff_rms = abs(f1[0] - f2[0])
    diff_p2p = abs(f1[3] - f2[3])

    return f1 + f2 + [diff_rms, diff_p2p]

# ==========================================
# MAIN SIMULATION LOOP
# ==========================================
def main():
    print("========================================")
    print("    BCI WHEELCHAIR: NOISE REJECTION     ")
    print("========================================\n")
    
    pilot = input("Enter Pilot Name (e.g., pralhad): ").strip().lower()
    
    model_path = f"{pilot}_model.pkl"
    scaler_path = f"{pilot}_scaler.pkl"
    
    if not os.path.exists(model_path):
        print(f"❌ Error: {model_path} not found. Run train_model.py first!")
        return

    # --- HARDWARE CONNECTION ---
    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        print("Connecting to Arduino... Please wait 4 seconds for R4 boot sequence.")
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE)
        time.sleep(4) 
        print(f"✅ Hardware Connected! Brain Loaded for {pilot.upper()}.")
    except PermissionError:
        print("\n[FATAL ERROR] ACCESS DENIED. Close Arduino IDE Serial Monitor!")
        return
    except Exception as e:
        print(f"Connection Error: {e}"); return

    # --- PYGAME SETUP ---
    pygame.init()
    WIDTH, HEIGHT = 900, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"NeuroDrive BCI - {pilot.capitalize()}")
    
    font_main = pygame.font.SysFont("Arial", 22, bold=True)
    font_small = pygame.font.SysFont("Arial", 16)
    
    wc_x, wc_y, wc_angle = WIDTH // 2, HEIGHT // 2 + 50, 0
    wc_speed = 0
    is_moving_forward = False  
    last_sent_led_cmd = 'C' 
    
    raw_buffer = deque(maxlen=WINDOW_SIZE)
    action_buffer = deque(maxlen=ACTION_BUFFER_SIZE) # Replaced vote_buffer
    
    current_probs = {}
    current_cmd = "RELAX"
    running, clock = True, pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        # 1. Read Serial Data
        while ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if "," in line:
                try:
                    raw_buffer.append([int(x) for x in line.split(",")])
                except: pass

        # 2. AI Inference
        if len(raw_buffer) == WINDOW_SIZE:
            feat = extract_live_features(raw_buffer)
            feat_scaled = scaler.transform([feat])
            
            prob_dict = dict(zip(model.classes_, model.predict_proba(feat_scaled)[0]))
            boosted = {
                'LEFT_WINK': prob_dict.get('LEFT_WINK', 0) * WINK_BOOST,
                'RIGHT_WINK': prob_dict.get('RIGHT_WINK', 0) * WINK_BOOST,
                'DOUBLE_BLINK': prob_dict.get('DOUBLE_BLINK', 0) * BLINK_BOOST,
                'JAW_CLENCH': prob_dict.get('JAW_CLENCH', 0) * CLENCH_BOOST,
                'RELAX': prob_dict.get('RELAX', 0)
            }
            
            current_probs = boosted 
            winner = max(boosted, key=boosted.get)
            
            if boosted[winner] >= CONFIDENCE_THRESHOLD:
                action_buffer.append(winner)
            else:
                action_buffer.append("RELAX")

        # 3. Physics & Noise Rejection Filter
        if len(action_buffer) == ACTION_BUFFER_SIZE:
            # Update UI with the most common thought right now
            current_cmd = max(set(action_buffer), key=action_buffer.count)
            
            # Count how many times each action appeared in the last 15 frames
            clench_count = action_buffer.count('JAW_CLENCH')
            blink_count = action_buffer.count('DOUBLE_BLINK')
            left_count = action_buffer.count('LEFT_WINK')
            right_count = action_buffer.count('RIGHT_WINK')

            led_cmd = 'C' 
            
            # --- THE BRAKES (Ultra-fast, needs only 3/15 frames) ---
            if blink_count >= 3:
                is_moving_forward = False
                led_cmd = 'B' 
                
            # --- THE GAS PEDAL (Deliberate hold, needs 10/15 frames) ---
            elif clench_count >= 10:
                is_moving_forward = True 
                
            # --- STEERING (Deliberate hold, needs 8/15 frames) ---
            if left_count >= 8: 
                wc_angle -= TURN_SPEED
                led_cmd = 'L' 
            elif right_count >= 8: 
                wc_angle += TURN_SPEED
                led_cmd = 'R' 
            elif is_moving_forward and led_cmd != 'B':
                led_cmd = 'F' # Point forward if driving straight

            # Update Hardware LED
            if led_cmd != last_sent_led_cmd:
                try:
                    ser.write(led_cmd.encode('utf-8'))
                    last_sent_led_cmd = led_cmd
                except: pass

            wc_speed = MAX_SPEED if is_moving_forward else 0

        # 4. Movement Calculation
        rad = np.radians(wc_angle)
        wc_x += wc_speed * np.sin(rad)
        wc_y -= wc_speed * np.cos(rad)
        wc_x, wc_y = max(20, min(WIDTH-20, wc_x)), max(20, min(HEIGHT-20, wc_y))

        # 5. Rendering
        screen.fill((255, 255, 255))
        color = (50, 200, 50) if is_moving_forward else (50, 50, 200)
        pygame.draw.circle(screen, color, (int(wc_x), int(wc_y)), 20)
        indicator_x = wc_x + 30 * np.sin(rad)
        indicator_y = wc_y - 30 * np.cos(rad)
        pygame.draw.line(screen, (200, 50, 50), (wc_x, wc_y), (indicator_x, indicator_y), 5)
        
        # HUD Elements
        pygame.draw.rect(screen, (240, 240, 240), (10, 10, 300, 200), border_radius=10)
        pygame.draw.rect(screen, (200, 200, 200), (10, 10, 300, 35), border_radius=10)
        screen.blit(font_main.render("LIVE BRAIN MONITOR", True, (50, 50, 50)), (25, 15))
        
        y_offset = 55
        for cls, p in current_probs.items():
            bar_color = (0, 150, 0) if cls == current_cmd else (100, 100, 100)
            pygame.draw.rect(screen, (200, 200, 200), (140, y_offset + 5, 140, 12))
            pygame.draw.rect(screen, bar_color, (140, y_offset + 5, int(min(140, p * 70)), 12))
            screen.blit(font_small.render(f"{cls}:", True, (0, 0, 0)), (20, y_offset))
            y_offset += 25

        pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 250, 10, 240, 100), border_radius=10)
        screen.blit(font_main.render(f"CMD: {current_cmd}", True, (255, 255, 255)), (WIDTH - 230, 25))
        drive_state = "DRIVING" if is_moving_forward else "STOPPED"
        state_color = (0, 255, 0) if is_moving_forward else (255, 100, 100)
        screen.blit(font_main.render(f"STATE: {drive_state}", True, state_color), (WIDTH - 230, 60))

        pygame.display.flip()
        clock.tick(60)

    # --- SHUTDOWN SEQUENCE ---
    print("🛑 Shutting down simulation...")
    try:
        ser.write('C'.encode('utf-8'))
        time.sleep(0.5) 
        print("💡 LED Matrix cleared.")
    except:
        pass

    ser.close()
    pygame.quit()
    print("✅ System offline.")

if __name__ == '__main__':
    main()
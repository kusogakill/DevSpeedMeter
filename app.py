import time
import threading
from pynput import keyboard
import sys

SMOOTH_ALPHA = 0.3
SPEED_SCALE = 12
ALERT_THRESHOLD = 100

state_lock = threading.Lock()
keys_count = 0
last_input = time.time()
last_second = time.time()
kps_value = 0
shutdown = False

def on_key(key):
    global keys_count, last_input
    with state_lock:
        keys_count += 1
        last_input = time.time()

def on_move(x, y):
    global last_input
    with state_lock:
        last_input = time.time()

kb_listener = keyboard.Listener(on_press=on_key)
kb_listener.daemon = True
kb_listener.start()

smoothed_kps = 0
alerted = False

try:
    while not shutdown:
        time.sleep(0.1)
        now = time.time()

        if now - last_second >= 1.0:
            with state_lock:
                kps_value = keys_count
                keys_count = 0
            last_second = now

        with state_lock:
            idle = now - last_input

        smoothed_kps = SMOOTH_ALPHA * kps_value + (1 - SMOOTH_ALPHA) * smoothed_kps
        speed = max(0, SPEED_SCALE * smoothed_kps - SPEED_SCALE)
        
        rpm = int(kps_value * 30)
        
        if speed < 20:
            gear = "1st"
        elif speed < 40:
            gear = "2nd"
        elif speed < 60:
            gear = "3rd"
        elif speed < 80:
            gear = "4th"
        else:
            gear = "5th"
        
        power = int(smoothed_kps * 5)

        bar_len = min(30, int(speed / 180 * 30))
        bar = "█" * bar_len + "░" * (30 - bar_len)
        
        status = "[OVER]" if speed >= ALERT_THRESHOLD and not alerted else ("[ZONE]" if speed >= 80 else ("[IDLE]" if idle > 30 else "[OK]"))
        
        output = f"[{bar}] {speed:6.1f} km/h | RPM: {rpm:5d} | {gear:>4s} | Power: {power:3d}% | Keys: {kps_value:4d} | Idle: {idle:5.1f}s | {status}"

        sys.stdout.write(f'\r{output}')
        sys.stdout.flush()
        
        if speed >= ALERT_THRESHOLD and not alerted:
            alerted = True
        if speed < 100:
            alerted = False

except KeyboardInterrupt:
    shutdown = True
    print("\n\nShutting down...")
    kb_listener.stop()
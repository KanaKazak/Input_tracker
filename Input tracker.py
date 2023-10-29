import time
import openpyxl
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
from pynput.keyboard import Key
from inputs import get_gamepad, UnpluggedError
import sys
# Initialize Excel workbook and worksheet
workbook = openpyxl.Workbook()
worksheet = workbook.active
worksheet.title = "InputData"
worksheet.append(["Time", "Event Type", "X", "Y", "Button/Key"])
input_count = 0
start_time = time.time()
is_running = True
ender_key = Key.f12
input_delay = 0.1
left_stick_last_moved = 0
right_stick_last_moved = 0
left_shoulder_last_moved = 0
right_shoulder_last_moved = 0
cooldown_period = 1
gamepad_tracking = False
def stop_listening():
    global is_running
    is_running = False
    global gamepad_tracking
    gamepad_tracking = False
    mouse_listener.stop()
    keyboard_listener.stop()
def record_input(event_type, x, y, action):
    global input_count
    input_count += 1
    current_time = time.time()
    worksheet.append([current_time, event_type, x, y, action])
def on_mouse_click(x, y, button, pressed):
    if pressed:
        event_type = "Mouse Click"
        action = f"Mouse {button} Pressed"
        record_input(event_type, x, y, action)
        print(f"Mouse clicked at ({x}, {y}) with {button}")
def on_key_press(key):
    event_type = "Key Press"
    try:
        action = f"Key Pressed: {key.char}"
        print(f"Key pressed: {key.char}")
    except AttributeError:
        action = f"Special Key Pressed: {key}"
        print(f"Special key pressed: {key}")
        if key == ender_key:  # Use the F12 key to stop
            end_time = time.time()
            time_elapsed = end_time - start_time
            input_rate = input_count / time_elapsed
            worksheet.append(["Time Elapsed (seconds)", time_elapsed])
            worksheet.append(["Input Count", input_count])
            worksheet.append(["Input Rate (inputs/sec)", input_rate])
            workbook.save("InputData.xlsx")
            print(f"{key} key was pressed, exiting program.")
            stop_listening()
    record_input(event_type, None, None, action)
def on_gamepad_input(event):
    global left_stick_last_moved, right_stick_last_moved, left_shoulder_last_moved, right_shoulder_last_moved
    if event.ev_type == "Absolute":
        if event.code == "ABS_X" or event.code == "ABS_Y":
            # Left stick moved
            current_time = time.time()
            if current_time - left_stick_last_moved >= cooldown_period:
                action = f"Left Stick Moved: {event.code}"
                print(action)
                left_stick_last_moved = current_time
                record_input("Gamepad Input", None, None, action)
        elif event.code == "ABS_RX" or event.code == "ABS_RY":
            # Right stick moved
            current_time = time.time()
            if current_time - right_stick_last_moved >= cooldown_period:
                action = f"Right Stick Moved: {event.code}"
                print(action)
                right_stick_last_moved = current_time
                record_input("Gamepad Input", None, None, action)
        elif event.code == "ABS_HAT0X" or event.code == "ABS_HAT0Y":
            # D-pad input
            action = f"Gamepad D-pad: {event.code} {'pressed' if event.state == 1 else 'released'}"
            print(action)
            record_input("Gamepad Input", None, None, action)
        elif event.code == "ABS_RZ":
            current_time = time.time()
            if current_time - right_shoulder_last_moved >= cooldown_period:
                action = f"Right Shoulder Moved: {event.code}"
                print(action)
                right_shoulder_last_moved = current_time
                record_input("Gamepad Input", None, None, action)
        elif event.code == "ABS_Z":
            current_time = time.time()
            if current_time - left_shoulder_last_moved >= cooldown_period:
                action = f"Left Shoulder Moved: {event.code}"
                print(action)
                left_shoulder_last_moved = current_time
                record_input("Gamepad Input", None, None, action)
    elif event.ev_type == "Key":
        action = f"Gamepad Button: {event.code} {'pressed' if event.state == 1 else 'released'}"
        print(action)
        record_input("Gamepad Input", None, None, action)
mouse_listener = MouseListener(on_click=on_mouse_click)
keyboard_listener = KeyboardListener(on_press=on_key_press)
mouse_listener.start()
keyboard_listener.start()
try:
    events = get_gamepad()
    gamepad_tracking = True  # Set the flag if a gamepad is found
except UnpluggedError:
    print("No gamepad found. Gamepad tracking is disabled.")
while is_running:
    # Check if a gamepad is found at regular intervals
    try:
        events = get_gamepad()
        gamepad_tracking = True  # Set the flag if a gamepad is found
    except UnpluggedError:
        gamepad_tracking = False  # Disable gamepad tracking if no gamepad is found
    if gamepad_tracking:
        try:
            events = get_gamepad()
            for event in events:
                on_gamepad_input(event)
        except UnpluggedError:
            print("Gamepad disconnected. Disabling gamepad tracking.")
            gamepad_tracking = False
sys.exit(0)
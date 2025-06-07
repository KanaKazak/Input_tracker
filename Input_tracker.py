import time
import sqlite3
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
from pynput.keyboard import Key
from inputs import get_gamepad, UnpluggedError
import threading
import tkinter as tk
from tkinter import ttk
from playsound import playsound
import os

# Thread-safe database connection
# Using a lock to ensure that database writes are thread-safe
db_lock = threading.Lock()

# Global control flags and config
mouse_listener = None
keyboard_listener = None
is_running = True
ender_key = Key.f12
input_delay = 0.1
cooldown_period = 1  # Cooldown for repeated gamepad inputs

# Input tracking stats
input_count = 0
start_time = time.time()

# Timestamps to debounce gamepad inputs
left_stick_last_moved = 0
right_stick_last_moved = 0
left_shoulder_last_moved = 0
right_shoulder_last_moved = 0

# Gamepad tracking flag
gamepad_tracking = False

# Initialize the database
# This function sets up the SQLite database and creates the input_data table if it doesn't exist
def setup_database():
    conn = sqlite3.connect('input_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS input_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            detail TEXT,
            timestamp REAL
        )
    ''')
    conn.commit()
    conn.close()

# Record input data into the database
# This function records input events into the database with a timestamp
def record_input(event_type, x, y, action):
    global input_count
    input_count += 1
    current_time = time.time()
    detail = action if action else f"{x}, {y}"

    with db_lock:
        with sqlite3.connect("input_data.db", check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO input_data (type, detail, timestamp) VALUES (?, ?, ?)",
                (event_type, detail, current_time)
            )
            conn.commit()
            print(f"Recorded: {event_type} - {detail}")

# Show a summary window with the tracked input data
# This function creates a tkinter window to display the summary of inputs tracked
def show_summary_window():
    global start_time
    # Read values from the database
    conn = sqlite3.connect('input_data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM input_data WHERE type = 'keyboard'")
    key_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM input_data WHERE type = 'mouse'")
    mouse_click_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM input_data WHERE type = 'gamepad'")
    gamepad_input_count = cursor.fetchone()[0]

    total_time = time.time() - start_time
    inputs_per_second = input_count / total_time if total_time > 0 else 0
    conn.close()

    # Create a summary window using tkinter
    window = tk.Tk()
    window.title("Input Tracker Summary")
    window.lift()
    window.attributes("-topmost", True)
    window.after_idle(window.attributes, "-topmost", False)


    # Set the window size and disable resizing
    window.geometry("400x300")  # Increased size
    window.resizable(False, False)

    # Center the window on the screen
    window.eval('tk::PlaceWindow . center')

    # Display the tracked values
    summary_text = (
        f"Keyboard inputs: {key_count}\n"
        f"Mouse clicks: {mouse_click_count}\n"
        f"Gamepad inputs: {gamepad_input_count}\n"
        f"Total time: {total_time:.2f} seconds\n"
        f"Total inputs: {input_count}\n"
        f"Inputs per second: {inputs_per_second:.2f}\n"
    )
    
    # Create a label to show the summary
    label = ttk.Label(window, text=summary_text, font=("Arial", 13), justify="center")
    label.pack(pady=30, padx=20)

    # Add an OK button to close the window, with more padding
    ok_button = ttk.Button(window, text="OK", command=window.destroy)
    ok_button.pack(pady=20, ipadx=20, ipady=10)

    # Start the tkinter main loop
    window.mainloop()

# Stop listening for inputs and show the summary window
# This function stops the input listeners and shows a summary of the tracked inputs
def stop_listening():
    # Play end sound
    playsound(os.path.join(os.path.dirname(__file__), 'D:/Audiofiles/end.mp3'))
    global is_running
    is_running = False
    global gamepad_tracking
    gamepad_tracking = False

    # Stop listeners
    if mouse_listener is not None:
        mouse_listener.stop()
    if keyboard_listener is not None:
        keyboard_listener.stop()

    # Show summary before exiting
    show_summary_window()

# Handle mouse click events
# This function records mouse click events and prints the coordinates and button pressed
def on_mouse_click(x, y, button, pressed):
    if pressed:
        record_input("mouse", x, y, f"Mouse {button} Pressed")
        print(f"Mouse clicked at ({x}, {y}) with {button}")

# Handle keyboard key press events
# This function records keyboard key presses and prints the key pressed
def on_key_press(key):
    key_type = 'keyboard'

    try:
        detail = key.char  # this works for normal keys
        action = f"Key Pressed: {detail}"
    except AttributeError:
        detail = str(key)  # fallback for special keys like F12
        action = f"Special Key Pressed: {detail}"

    print(action)
    record_input(key_type, None, None, action)

    if key == Key.f12:
        stop_listening()
        return False  # stop the keyboard listener
    
# Handle gamepad input
def on_gamepad_input(event):
    #Process a single gamepad event.
    global left_stick_last_moved, right_stick_last_moved
    global left_shoulder_last_moved, right_shoulder_last_moved

    if event.ev_type == "Absolute":
        current_time = time.time()
        if event.code in ("ABS_X", "ABS_Y"):
            if current_time - left_stick_last_moved >= cooldown_period:
                left_stick_last_moved = current_time
                action = f"Left Stick Moved: {event.code}"
                record_input("gamepad", None, None, action)
                print(action)
        elif event.code in ("ABS_RX", "ABS_RY"):
            if current_time - right_stick_last_moved >= cooldown_period:
                right_stick_last_moved = current_time
                action = f"Right Stick Moved: {event.code}"
                record_input("gamepad", None, None, action)
                print(action)
        elif event.code in ("ABS_Z",):
            if current_time - left_shoulder_last_moved >= cooldown_period:
                left_shoulder_last_moved = current_time
                action = f"Left Shoulder Moved: {event.code}"
                record_input("gamepad", None, None, action)
                print(action)
        elif event.code in ("ABS_RZ",):
            if current_time - right_shoulder_last_moved >= cooldown_period:
                right_shoulder_last_moved = current_time
                action = f"Right Shoulder Moved: {event.code}"
                record_input("gamepad", None, None, action)
                print(action)
        elif event.code in ("ABS_HAT0X", "ABS_HAT0Y"):
            if event.code == "ABS_HAT0X":
                direction = {
                    -1: 'left',
                    0: 'centered',
                    1: 'right'
                }.get(event.state, 'unknown')
            else:  # ABS_HAT0Y
                direction = {
                    -1: 'up',
                    0: 'centered',
                    1: 'down'
                }.get(event.state, 'unknown')
            
            action = f"Gamepad D-pad: {event.code} → {direction}"
            record_input("gamepad", None, None, action)
            print(action)
    elif event.ev_type == "Key":
        action = f"Gamepad Button: {event.code} {'pressed' if event.state == 1 else 'released'}"
        record_input("gamepad", None, None, action)
        print(action)

# Main function to set up the database and start input listeners
# This function initializes the database, starts the mouse and keyboard listeners, and handles gamepad input
def main():
    # Play start sound
    playsound(os.path.join(os.path.dirname(__file__), 'D:/Audiofiles/start.mp3'))
    setup_database()
    global mouse_listener, keyboard_listener
    # Start listeners
    mouse_listener = MouseListener(on_click=on_mouse_click)
    keyboard_listener = KeyboardListener(on_press=on_key_press) # type: ignore
    mouse_listener.start()
    keyboard_listener.start()

    # Gamepad loop
    global gamepad_tracking
    try:
        get_gamepad()
        gamepad_tracking = True
    except UnpluggedError:
        print("No gamepad found. Gamepad tracking is disabled.")

    try:
        while is_running:
            if gamepad_tracking:
                try:
                    events = get_gamepad()
                    for event in events:
                        on_gamepad_input(event)
                except UnpluggedError:
                    print("Gamepad disconnected. Disabling gamepad tracking.")
                    gamepad_tracking = False
            else:
                try:
                    get_gamepad()
                    gamepad_tracking = True
                except UnpluggedError:
                    time.sleep(2)
            time.sleep(input_delay)
    except KeyboardInterrupt:
        stop_listening()

    # Wait for listeners to finish before exiting
    if mouse_listener is not None:
        mouse_listener.join()
    if keyboard_listener is not None:
        keyboard_listener.join()

    # Do not call sys.exit(0) here; let the script end naturally

if __name__ == "__main__":
    main()
import cv2 as cv
from cvzone.HandTrackingModule import HandDetector
import pyautogui
import time
import threading
from playsound import playsound
import tkinter as tk
from tkinter import messagebox
from pynput.keyboard import Key, Controller

# Initialize global variables
cap = None
detector = None
keyboard = Controller()
last_enter_press_time = 0
left_key_pressed = False
right_key_pressed = False
brake_location = None
gas_location = None
game_started = False
start_time = None
sound_played = False
running = False

# Initialize the hand detector
detector = HandDetector(detectionCon=0.7, maxHands=2)

# Cooldown settings
COOLDOWN_TIME = 0.1  # Reduced cooldown time

def update_locations():
    global brake_location, gas_location, game_started, start_time, sound_played
    while running:
        try:
            brake_location = pyautogui.locateOnScreen('C:/Users/ASUS/Desktop/Gesture/Game Automation/brake.png', confidence=0.7, grayscale=True)
            gas_location = pyautogui.locateOnScreen('C:/Users/ASUS/Desktop/Gesture/Game Automation/gas2.png', confidence=0.7, grayscale=True)
            
            if brake_location and gas_location and not game_started:
                game_started = True
                start_time = time.time()
                print("Game elements detected. Starting game mode in 3 seconds.")
                if not sound_played:
                    threading.Thread(target=playsound, args=('C:/Users/ASUS/Desktop/Gesture/Game Automation/game-countdown-62-199828.mp3',), daemon=True).start()
                    sound_played = True
            elif game_started and (not brake_location or not gas_location):
                game_started = False
                start_time = None
                sound_played = False
                print("Game elements no longer detected. Switching to navigation mode.")
        except pyautogui.ImageNotFoundException:
            if game_started:
                game_started = False
                start_time = None
                sound_played = False
                print("Game elements no longer detected. Switching to navigation mode.")
        time.sleep(1)  # Reduced frequency of checks

def process_hand(hand, current_time):
    global last_enter_press_time, left_key_pressed, right_key_pressed
    fingers = detector.fingersUp(hand)
    total_fingers = sum(fingers)
    
    if not game_started or (start_time and current_time - start_time < 3):
        if total_fingers == 3 and current_time - last_enter_press_time > COOLDOWN_TIME:
            keyboard.press(Key.enter)
            keyboard.release(Key.enter)
            last_enter_press_time = current_time
        elif hand["type"] == "Right":
            if total_fingers == 1:
                keyboard.press(Key.left)
                keyboard.release(Key.left)
            elif total_fingers == 2:
                keyboard.press(Key.right)
                keyboard.release(Key.right)
        elif hand["type"] == "Left":
            if total_fingers == 1:
                keyboard.press(Key.up)
                keyboard.release(Key.up)
            elif total_fingers == 2:
                keyboard.press(Key.down)
                keyboard.release(Key.down)
    elif game_started and current_time - start_time >= 3:
        if brake_location and fingers == [0, 0, 0, 0, 0]:
            if not left_key_pressed:
                keyboard.press(Key.left)
                left_key_pressed = True
        elif left_key_pressed:
            keyboard.release(Key.left)
            left_key_pressed = False

        if gas_location and fingers == [1, 1, 1, 1, 1]:
            if not right_key_pressed:
                keyboard.press(Key.right)
                right_key_pressed = True
        elif right_key_pressed:
            keyboard.release(Key.right)
            right_key_pressed = False

def start_gesture_control():
    global cap, running
    cap = cv.VideoCapture(0)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    running = True
    threading.Thread(target=run, daemon=True).start()
    threading.Thread(target=update_locations, daemon=True).start()

def run():
    global running
    while running:
        success, img = cap.read()
        if not success:
            break
        
        hands, img = detector.findHands(img, draw=True)
        
        current_time = time.time()
        
        if hands:
            threads = []
            for hand in hands:
                thread = threading.Thread(target=process_hand, args=(hand, current_time))
                thread.start()
                threads.append(thread)
            
            for thread in threads:
                thread.join()
        
        if game_started and current_time - start_time >= 3:
            cv.putText(img, "Game Started", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv.imshow("Webcam", img)
        
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

def stop_gesture_control():
    global cap, running
    running = False
    if cap:
        cap.release()
    cv.destroyAllWindows()
    messagebox.showinfo("Gesture Control", "Gesture control stopped.")

# Tkinter GUI
app = tk.Tk()
app.title("Hill Climb Racing Gesture Control")

start_button = tk.Button(app, text="Start Gesture Control", command=start_gesture_control)
start_button.pack(pady=20)

stop_button = tk.Button(app, text="Stop Gesture Control", command=stop_gesture_control)
stop_button.pack(pady=20)

app.mainloop()
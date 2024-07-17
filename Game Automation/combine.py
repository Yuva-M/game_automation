import cv2 as cv
from cvzone.HandTrackingModule import HandDetector
import pyautogui
import time
import threading
from playsound import playsound

# Initialize the webcam
cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

# Initialize the hand detector
detector = HandDetector(detectionCon=0.7, maxHands=2)

# Cooldown settings
COOLDOWN_TIME = 0.5
last_enter_press_time = 0

# Variables to track key states and button locations
left_key_pressed = False
right_key_pressed = False
brake_location = None
gas_location = None
game_started = False
start_time = None
sound_played = False

# Function to update button locations periodically
def update_locations():
    global brake_location, gas_location, game_started, start_time, sound_played
    while True:
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
        time.sleep(0.2)

# Start the location update thread
threading.Thread(target=update_locations, daemon=True).start()

while True:
    success, img = cap.read()
    if not success:
        break
    
    hands, img = detector.findHands(img, draw=True)  # Changed to draw=True
    
    current_time = time.time()
    
    if hands:
        for hand in hands:
            fingers = detector.fingersUp(hand)
            total_fingers = sum(fingers)
            
            # Add hand label
            x, y = hand['lmList'][0][:2]
            cv.putText(img, hand['type'], (x, y - 20), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            if not game_started or (start_time and current_time - start_time < 3):
                if total_fingers == 3:
                    if current_time - last_enter_press_time > COOLDOWN_TIME:
                        pyautogui.press('enter')
                        last_enter_press_time = current_time
                elif hand["type"] == "Right":
                    if total_fingers == 1:
                        pyautogui.press('left')
                    elif total_fingers == 2:
                        pyautogui.press('right')
                elif hand["type"] == "Left":
                    if total_fingers == 1:
                        pyautogui.press('up')
                    elif total_fingers == 2:
                        pyautogui.press('down')
            elif game_started and current_time - start_time >= 3:
                if brake_location and fingers == [0, 0, 0, 0, 0]:
                    if not left_key_pressed:
                        pyautogui.keyDown('left')
                        left_key_pressed = True
                elif left_key_pressed:
                    pyautogui.keyUp('left')
                    left_key_pressed = False

                if gas_location and fingers == [1, 1, 1, 1, 1]:
                    if not right_key_pressed:
                        pyautogui.keyDown('right')
                        right_key_pressed = True
                elif right_key_pressed:
                    pyautogui.keyUp('right')
                    right_key_pressed = False
    
    # Display "Game Started" message
    if game_started and current_time - start_time >= 3:
        cv.putText(img, "Game Started", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv.imshow("Webcam", img)
    
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

# Ensure keys are released before exiting
if left_key_pressed:
    pyautogui.keyUp('left')
if right_key_pressed:
    pyautogui.keyUp('right')

cap.release()
cv.destroyAllWindows()
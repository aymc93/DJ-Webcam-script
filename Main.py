import cv2
import mediapipe as mp
import math
import numpy as np
import os
import vlc
import sys

# --- CONFIGURATION ---
MUSIC_FOLDER = "musique"
wCam, hCam = 640, 480




# --- VERIFICATIONS ---
if not os.path.exists(MUSIC_FOLDER):
    print(f"ERREUR: Le dossier '{MUSIC_FOLDER}' n'existe pas !")
    sys.exit()

files = [f for f in os.listdir(MUSIC_FOLDER) if f.endswith(('.mp3', '.wav'))]
if not files:
    print(f"ERREUR: Mets un MP3 dans le dossier '{MUSIC_FOLDER}' !")
    sys.exit()

song_path = os.path.join(MUSIC_FOLDER, files[0])
print(f"Chargement de : {files[0]}")





# --- VLC SETUP ---
try:
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(song_path)
    player.set_media(media)
    player.play()
    player.audio_set_volume(50)
except Exception as e:
    print("Erreur VLC:", e)
    sys.exit()

current_speed = 1.0



# --- MEDIAPIPE SETUP ---
mpHands = mp.solutions.hands
hands = mpHands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7
)
mpDraw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

def draw_bar(img, x, y, value, min_val, max_val, color, text):
    bar_height = 150
    ratio = (value - min_val) / (max_val - min_val)
    ratio = np.clip(ratio, 0, 1)
    fill_height = int(bar_height * ratio)
    cv2.rectangle(img, (x, y), (x + 20, y + bar_height), color, 2)
    cv2.rectangle(img, (x, y + bar_height - fill_height), (x + 20, y + bar_height), color, cv2.FILLED)
    cv2.putText(img, f'{text}', (x - 10, y + bar_height + 20), cv2.FONT_HERSHEY_PLAIN, 1, color, 1)

print("--- CONTROLES ---")
print("Main GAUCHE: Volume (Pincer)")
print("Main DROITE: Vitesse (Pincer)")
print("Appuie sur 'q' pour quitter")

while True:
    success, img = cap.read()
    if not success:
        print("Erreur caméra")
        break
    
    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    
    if results.multi_hand_landmarks:
        for handLms, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label
            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
            
            lmList = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                lmList.append([id, int(lm.x * w), int(lm.y * h)])
            
            if lmList:

                
                # Points 4 (Pouce) et 8 (Index)
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                length = math.hypot(x2 - x1, y2 - y1)
                
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)

                if label == 'Left':
                    vol = np.interp(length, [20, 200], [0, 100])
                    player.audio_set_volume(int(vol))
                    draw_bar(img, 50, 150, vol, 0, 100, (0, 255, 0), "Vol")
                elif label == 'Right':


                    # Vitesse entre 0.5x et 2.0x
                    speed = np.interp(length, [20, 200], [0.5, 2.0])


                    # Petit filtre pour éviter que le son saute
                    if abs(current_speed - speed) > 0.05:
                        current_speed = speed
                        player.set_rate(current_speed)
                    draw_bar(img, wCam - 70, 150, speed, 0.5, 2.0, (255, 0, 0), "Speed")

    cv2.imshow("DJ Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

player.stop()
cap.release()
cv2.destroyAllWindows()
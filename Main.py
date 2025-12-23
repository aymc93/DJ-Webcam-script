import cv2
import mediapipe as mp
import math
import numpy as np
import os
import vlc
import sys
import time

# --- CONFIGURATION ---
MUSIC_FOLDER = "musique"
wCam, hCam = 1280, 720  # HD
COOLDOWN_TIME = 2.0 

# --- COULEURS (BGR) ---
C_DARK = (20, 20, 20)
C_WHITE = (240, 240, 240)
C_NEON_BLUE = (255, 200, 0)   # Cyan (BGR)
C_NEON_GREEN = (50, 255, 50)  # Vert Matrix
C_NEON_PURPLE = (255, 0, 255) # Magenta
C_ALERT = (0, 0, 255)         # Rouge

# --- VERIFICATIONS ---
if not os.path.exists(MUSIC_FOLDER):
    print(f"ERREUR: Le dossier '{MUSIC_FOLDER}' n'existe pas !")
    sys.exit()

files = [f for f in os.listdir(MUSIC_FOLDER) if f.endswith(('.mp3', '.wav'))]
files.sort()
if not files:
    print(f"ERREUR: Dossier vide !")
    sys.exit()

# --- VARIABLES ---
current_song_index = 0
last_action_time = 0
current_volume = 50
target_speed = 1.0
is_in_effect = False 

# --- VLC SETUP ---
instance = vlc.Instance()
player = instance.media_player_new()

def play_song(index):
    global current_song_index, target_speed
    if index >= len(files): index = 0
    elif index < 0: index = len(files) - 1
        
    current_song_index = index
    song_path = os.path.join(MUSIC_FOLDER, files[current_song_index])
    
    media = instance.media_new(song_path)
    player.set_media(media)
    player.play()
    
    time.sleep(0.1)
    player.audio_set_volume(int(current_volume))
    player.set_rate(target_speed)

play_song(0)

# --- MEDIAPIPE ---
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

# --- FONCTION D'INTERFACE (HUD) ---
def draw_hud(img, vol, speed, song_name, effect_active):
    h, w, c = img.shape
    overlay = img.copy()
    
    # 1. BANDEAU DU HAUT (TITRE)
    cv2.rectangle(overlay, (0, 0), (w, 80), C_DARK, cv2.FILLED)
    
    # 2. BANDEAU DU BAS (LEGENDE)
    cv2.rectangle(overlay, (0, h-60), (w, h), C_DARK, cv2.FILLED)
    
    # 3. JAUGE VOLUME (GAUCHE)
    vol_height = int((vol/100) * 300)
    cv2.rectangle(overlay, (20, h//2 - 150), (60, h//2 + 150), C_DARK, cv2.FILLED) # Fond
    cv2.rectangle(overlay, (20, h//2 + 150 - vol_height), (60, h//2 + 150), C_NEON_GREEN, cv2.FILLED) # Niveau
    cv2.rectangle(overlay, (20, h//2 - 150), (60, h//2 + 150), C_WHITE, 2) # Bordure
    cv2.putText(img, "VOL", (20, h//2 - 160), cv2.FONT_HERSHEY_PLAIN, 1.5, C_WHITE, 2)
    cv2.putText(img, f"{int(vol)}%", (20, h//2 + 180), cv2.FONT_HERSHEY_PLAIN, 1.5, C_WHITE, 2)

    # 4. JAUGE VITESSE (DROITE)
    # Speed va de 0.5 à 2.0. On normalise.
    speed_ratio = (speed - 0.5) / 1.5
    speed_height = int(speed_ratio * 300)
    cv2.rectangle(overlay, (w-60, h//2 - 150), (w-20, h//2 + 150), C_DARK, cv2.FILLED)
    cv2.rectangle(overlay, (w-60, h//2 + 150 - speed_height), (w-20, h//2 + 150), C_NEON_BLUE, cv2.FILLED)
    cv2.rectangle(overlay, (w-60, h//2 - 150), (w-20, h//2 + 150), C_WHITE, 2)
    cv2.putText(img, "BPM", (w-65, h//2 - 160), cv2.FONT_HERSHEY_PLAIN, 1.5, C_WHITE, 2)
    cv2.putText(img, f"x{speed:.1f}", (w-65, h//2 + 180), cv2.FONT_HERSHEY_PLAIN, 1.5, C_WHITE, 2)

    # APPLIQUER LA TRANSPARENCE
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

    # TEXTES
    cv2.putText(img, "DJ CONTROL CENTER", (w//2 - 150, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, C_NEON_BLUE, 1)
    cv2.putText(img, song_name, (50, 65), cv2.FONT_HERSHEY_DUPLEX, 1.0, C_WHITE, 2)
    
    legend = "GAUCHE: Pincer=Vol | Plat=Matrix       DROITE: Pincer=Vitesse | Pinky=Suivant"
    cv2.putText(img, legend, (50, h-20), cv2.FONT_HERSHEY_PLAIN, 1.2, C_WHITE, 1)

    # EFFET MATRIX OVERLAY
    if effect_active:
        cv2.rectangle(img, (0, 0), (w, h), (0, 255, 0), 10) # Cadre vert
        cv2.putText(img, "MATRIX EFFECT ACTIVATED", (w//2 - 300, h//2), cv2.FONT_HERSHEY_COMPLEX, 2.0, C_NEON_GREEN, 3)
        cv2.putText(img, "SLOW MOTION...", (w//2 - 150, h//2 + 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, C_WHITE, 2)

while True:
    success, img = cap.read()
    if not success: break
    
    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    
    effect_active_this_frame = False
    h, w, c = img.shape 

    if results.multi_hand_landmarks:
        for handLms, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label
            
            # Dessin des mains discret
            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS, 
                                  mpDraw.DrawingSpec(color=(100,100,100), thickness=2, circle_radius=2),
                                  mpDraw.DrawingSpec(color=(200,200,200), thickness=2, circle_radius=2))
            
            lmList = []
            for id, lm in enumerate(handLms.landmark):
                lmList.append([id, int(lm.x * w), int(lm.y * h)])
            
            if lmList:
                x4, y4 = lmList[4][1], lmList[4][2]     # Pouce
                x8, y8 = lmList[8][1], lmList[8][2]     # Index
                x12, y12 = lmList[12][1], lmList[12][2] # Majeur
                x20, y20 = lmList[20][1], lmList[20][2] # Pinky
                x0, y0 = lmList[0][1], lmList[0][2]     # Poignet

                length_index = math.hypot(x8 - x4, y8 - y4)
                
                # --- MAIN GAUCHE ---
                if label == 'Left':
                    diff_hauteur = abs(y0 - y12)
                    largeur_main = abs(x0 - x12)

                    # Si main horizontale (MATRIX)
                    if diff_hauteur < 60 and largeur_main > 80:
                        effect_active_this_frame = True
                        player.set_rate(0.3)
                        cv2.line(img, (x0, y0), (x12, y12), C_NEON_GREEN, 5)

                    else:
                        # VOLUME
                        vol = np.interp(length_index, [20, 200], [0, 100])
                        current_volume = vol
                        player.audio_set_volume(int(vol))
                        if length_index < 200:
                            cv2.line(img, (x4, y4), (x8, y8), C_NEON_GREEN, 3)
                            cv2.circle(img, ((x4+x8)//2, (y4+y8)//2), 10, C_NEON_GREEN, cv2.FILLED)

                # --- MAIN DROITE ---
                elif label == 'Right':
                    # VITESSE
                    speed = np.interp(length_index, [20, 200], [0.5, 2.0])
                    if abs(target_speed - speed) > 0.05:
                        target_speed = speed
                    
                    if not effect_active_this_frame:
                         player.set_rate(target_speed)

                    if length_index < 200:
                        cv2.line(img, (x4, y4), (x8, y8), C_NEON_BLUE, 3)
                        cv2.circle(img, ((x4+x8)//2, (y4+y8)//2), 10, C_NEON_BLUE, cv2.FILLED)

                    # SUIVANT
                    length_pinky = math.hypot(x20 - x4, y20 - y4)
                    if length_pinky < 30 and (time.time() - last_action_time) > COOLDOWN_TIME:
                        play_song(current_song_index + 1)
                        last_action_time = time.time()
                        cv2.circle(img, (x20, y20), 25, C_NEON_PURPLE, cv2.FILLED)
                        # --- CORRECTION ICI (FONT_HERSHEY_DUPLEX) ---
                        cv2.putText(img, "NEXT!", (x20, y20-40), cv2.FONT_HERSHEY_DUPLEX, 1, C_NEON_PURPLE, 2)

    # Gestion fin effet Matrix
    if not effect_active_this_frame and is_in_effect:
        player.set_rate(target_speed)
    is_in_effect = effect_active_this_frame

    # INTERFACE
    draw_hud(img, current_volume, target_speed, files[current_song_index], is_in_effect)

    cv2.imshow("DJ Control - GUI EDITION", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

player.stop()
cap.release()
cv2.destroyAllWindows()
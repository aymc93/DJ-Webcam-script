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
wCam, hCam = 640, 480
COOLDOWN_TIME = 2.0  # Temps d'attente entre deux changements de musique (secondes)

# --- VERIFICATIONS DOSSIER ---
if not os.path.exists(MUSIC_FOLDER):
    print(f"ERREUR: Le dossier '{MUSIC_FOLDER}' n'existe pas !")
    sys.exit()

# On charge TOUTES les musiques
files = [f for f in os.listdir(MUSIC_FOLDER) if f.endswith(('.mp3', '.wav'))]
files.sort() # On les trie par ordre alphabétique

if not files:
    print(f"ERREUR: Mets des MP3 dans le dossier '{MUSIC_FOLDER}' !")
    sys.exit()

print(f"Playlist chargée : {len(files)} titres.")

# --- VARIABLES GLOBALES ---
current_song_index = 0
last_change_time = 0
current_volume = 50
current_speed = 1.0

# --- SETUP VLC ---
instance = vlc.Instance()
player = instance.media_player_new()

def play_song(index):
    global current_song_index, current_speed
    
    # Gestion de la boucle (si on arrive à la fin, on revient au début)
    if index >= len(files):
        index = 0
    elif index < 0:
        index = len(files) - 1
        
    current_song_index = index
    song_path = os.path.join(MUSIC_FOLDER, files[current_song_index])
    
    print(f"Lecture de : {files[current_song_index]}")
    
    media = instance.media_new(song_path)
    player.set_media(media)
    player.play()
    
    # On remet le volume et la vitesse (VLC reset la vitesse à chaque changement)
    time.sleep(0.1) # Petit délai pour que VLC charge
    player.audio_set_volume(int(current_volume))
    player.set_rate(current_speed)

# Lancer la première musique
play_song(0)

# --- MEDIAPIPE SETUP ---
mpHands = mp.solutions.hands
hands = mpHands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7
)
mpDraw = mp.solutions.drawing_utils

# --- CAMERA ---
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

print("\n--- CONTROLES ---")
print("🖐  Main GAUCHE (Pouce-Index)  = Volume")
print("🖐  Main DROITE (Pouce-Index)  = Vitesse")
print("⏭️  Main DROITE (Pouce-PINKY)  = Musique Suivante")
print("❌  Touche 'q' pour quitter")

while True:
    success, img = cap.read()
    if not success: break
    
    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    
    # Afficher le titre en cours sur l'écran
    cv2.putText(img, f"Titre: {files[current_song_index]}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    if results.multi_hand_landmarks:
        for handLms, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label
            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
            
            lmList = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                lmList.append([id, int(lm.x * w), int(lm.y * h)])
            
            if lmList:
                # Coordonnées des bouts des doigts
                x_pouce, y_pouce = lmList[4][1], lmList[4][2]
                x_index, y_index = lmList[8][1], lmList[8][2]
                x_pinky, y_pinky = lmList[20][1], lmList[20][2] # Bout du petit doigt

                # Calcul distance Pouce-Index (Pour Volume/Vitesse)
                length_index = math.hypot(x_index - x_pouce, y_index - y_pouce)
                
                # MAIN GAUCHE : VOLUME
                if label == 'Left':
                    cx, cy = (x_pouce + x_index) // 2, (y_pouce + y_index) // 2
                    cv2.line(img, (x_pouce, y_pouce), (x_index, y_index), (0, 255, 0), 3)
                    
                    vol = np.interp(length_index, [20, 200], [0, 100])
                    current_volume = vol
                    player.audio_set_volume(int(vol))
                    draw_bar(img, 50, 150, vol, 0, 100, (0, 255, 0), "Vol")

                # MAIN DROITE
                elif label == 'Right':
                    # 1. CONTROLE VITESSE (Pouce-Index)
                    cv2.line(img, (x_pouce, y_pouce), (x_index, y_index), (255, 0, 0), 3)
                    speed = np.interp(length_index, [20, 200], [0.5, 2.0])
                    
                    if abs(current_speed - speed) > 0.05:
                        current_speed = speed
                        player.set_rate(current_speed)
                    draw_bar(img, wCam - 70, 150, speed, 0.5, 2.0, (255, 0, 0), "Speed")

                    # 2. CONTROLE SUIVANT (Pouce-Pinky)
                    # On calcule la distance entre le Pouce (4) et le Petit Doigt (20)
                    length_pinky = math.hypot(x_pinky - x_pouce, y_pinky - y_pouce)
                    
                    # Si pincement détecté (< 30 pixels) ET que le temps d'attente est passé
                    if length_pinky < 30 and (time.time() - last_change_time) > COOLDOWN_TIME:
                        print(">>> NEXT SONG ! >>>")
                        play_song(current_song_index + 1)
                        last_change_time = time.time() # Reset du chrono
                        
                        # Petit feedback visuel (Cercle Jaune)
                        cv2.circle(img, (x_pinky, y_pinky), 15, (0, 255, 255), cv2.FILLED)

    cv2.imshow("DJ Control - Next Gen", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

player.stop()
cap.release()
cv2.destroyAllWindows()
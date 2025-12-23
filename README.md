# 🎵 AI Gesture DJ

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.9-orange?style=for-the-badge&logo=google)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green?style=for-the-badge&logo=opencv)

**Transformez votre webcam en table de mixage futuriste.**
Ce projet utilise l'intelligence artificielle (MediaPipe) pour détecter vos mains et contrôler votre musique sans toucher le clavier. Volume, vitesse (BPM) et effets spéciaux sont pilotés par de simples gestes.

---

## 📸 Aperçu

L'interface **HUD (Head-Up Display)** se superpose à votre caméra pour un contrôle immersif :

* **Jauges Dynamiques :** Visualisez le volume et la vitesse en temps réel.
* **Feedback Visuel :** Des lasers néons suivent vos doigts.
* **Mode Nuit :** Interface sombre et semi-transparente style "Cyberpunk".

---

## 🎮 Commandes Gestuelles

Le système distingue la main gauche de la main droite pour offrir des contrôles séparés.

### 🖐 Main GAUCHE (Mixage & Effets)

| Geste | Action | Description |
| :--- | :--- | :--- |
| **Pincement** (Pouce-Index) | **Volume** 🔊 | Écartez les doigts pour monter le son, rapprochez-les pour baisser. |
| **Main à Plat** (Horizontale) | **Matrix Effect** 📉 | Active un ralenti extrême (Slow Motion) tant que la main est maintenue. |

### 🖐 Main DROITE (Rythme & Navigation)

| Geste | Action | Description |
| :--- | :--- | :--- |
| **Pincement** (Pouce-Index) | **Vitesse (BPM)** ⏩ | Changez le tempo de 0.5x à 2.0x en temps réel (Pitch Shift). |
| **Contact** (Pouce-Petit Doigt) | **Suivant** ⏭️ | Passez à la musique suivante (Cooldown de 2s). |

---

## 🚀 Installation

### Prérequis
* Une webcam fonctionnelle.
* Python 3.10 ou supérieur (recommandé via Conda sur Kali Linux).
* VLC Media Player installé sur votre système.

### 1. Cloner le projet
```bash
git clone [https://github.com/VOTRE_NOM_UTILISATEUR/AI-Gesture-DJ.git](https://github.com/VOTRE_NOM_UTILISATEUR/AI-Gesture-DJ.git)
cd AI-Gesture-DJ

2. Créer l'environnement (Recommandé)
Bash

# Avec Conda (pour éviter les conflits de version)
conda create -n musique -c conda-forge python=3.10 pip -y
conda activate musique

3. Installer les dépendances
Bash

# Installation des librairies spécifiques
pip install opencv-python mediapipe==0.10.9 python-vlc numpy
pip install "protobuf<3.20"  # Crucial pour la compatibilité MediaPipe

4. Ajouter de la musique

Créez un dossier nommé musique à la racine du projet et déposez-y vos fichiers .mp3 ou .wav.
Bash

mkdir musique
# Copiez vos fichiers dedans

▶️ Utilisation

Lancez simplement le script principal :
Bash

python Main.py

    Appuyez sur 'q' pour quitter l'application proprement.

🛠 Technologies

    MediaPipe Hands : Pour le tracking haute précision des articulations de la main.

    OpenCV : Pour le traitement d'image et l'affichage de l'interface graphique (HUD).

    Python-VLC : Wrapper pour contrôler le moteur audio de VLC.

    NumPy : Pour les interpolations mathématiques fluides (mapping des distances).

⚠️ Dépannage (Kali Linux / Linux)

Si vous rencontrez des erreurs de type AttributeError: module 'mediapipe' has no attribute 'solutions', c'est souvent un conflit de version avec Protobuf.

Assurez-vous d'avoir exécuté :
Bash

pip install "protobuf<3.20" --force-reinstall

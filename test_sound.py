"""test_sound.py - jalankan dari folder Proyek_Battleship_AI untuk test sound effects.
Ketik: python test_sound.py
"""
import time
import numpy as np
import pygame

pygame.init()
pygame.display.set_mode((300, 100))
pygame.display.set_caption("Sound Test")

# Init mixer stereo
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
print(f"Mixer: {pygame.mixer.get_init()}")


def make_stereo_sound(mono_float, volume=0.85):
    peak = np.abs(mono_float).max()
    if peak > 1e-9:
        mono_float = mono_float / peak
    mono = (mono_float * volume * 32767).clip(-32767, 32767).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack([mono, mono]))
    return pygame.sndarray.make_sound(stereo)


sr = 44100

# --- shoot ---
t = np.linspace(0, 0.30, int(sr * 0.30), endpoint=False)
boom  = np.sin(2 * np.pi * 85 * t) * np.exp(-t * 18)
noise = np.random.default_rng(1).uniform(-1, 1, len(t)) * np.exp(-t * 32) * 0.5
snd_shoot = make_stereo_sound(boom + noise, 0.72)

# --- hit ---
t = np.linspace(0, 0.45, int(sr * 0.45), endpoint=False)
boom    = np.sin(2 * np.pi * 58 * t) * np.exp(-t * 8)
crackle = np.random.default_rng(2).uniform(-1, 1, len(t)) * np.exp(-t * 6) * 0.55
mid     = np.sin(2 * np.pi * 300 * t) * np.exp(-t * 20) * 0.3
snd_hit = make_stereo_sound(boom + crackle + mid, 0.80)

# --- splash ---
t   = np.linspace(0, 0.40, int(sr * 0.40), endpoint=False)
env = np.exp(-t * 6) * (1 - np.exp(-t * 50))
noise  = np.random.default_rng(3).uniform(-1, 1, len(t)) * env
bubble = np.sin(2 * np.pi * 700 * t) * env * 0.28
snd_splash = make_stereo_sound(noise + bubble, 0.58)

# --- sunk ---
t     = np.linspace(0, 0.70, int(sr * 0.70), endpoint=False)
boom  = np.sin(2 * np.pi * 48 * t) * np.exp(-t * 5)
boom2 = np.sin(2 * np.pi * 110 * t) * np.exp(-t * 8) * 0.55
noise = np.random.default_rng(4).uniform(-1, 1, len(t)) * np.exp(-t * 4) * 0.65
snd_sunk = make_stereo_sound(boom + boom2 + noise, 0.90)

sounds = [("SHOOT (cannon)", snd_shoot),
          ("HIT (explosion)", snd_hit),
          ("SPLASH (miss)",   snd_splash),
          ("SUNK (big boom)", snd_sunk)]

print("Playing sounds with 1.2s gap each...\n")
for name, snd in sounds:
    print(f"  > {name}")
    snd.play()
    time.sleep(1.2)

print("\nDone! Close window to exit.")
running = True
while running:
    for ev in pygame.event.get():
        if ev.type in (pygame.QUIT, pygame.KEYDOWN):
            running = False
pygame.quit()

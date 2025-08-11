# utils/sound.py
import pygame
import os
from config import resource_path

# Инициализация pygame mixer
pygame.mixer.init()

# Загрузка звуков
SOUNDS = {
    'success': pygame.mixer.Sound(resource_path('data/sounds/agree.wav')),
    'error': pygame.mixer.Sound(resource_path('data/sounds/angry.wav')),
    'notification': pygame.mixer.Sound(resource_path('data/sounds/wonder.wav')),
    'callout': pygame.mixer.Sound(resource_path('data/sounds/callout.wav'))
}

# Установка громкости (0.0 до 1.0)
SOUNDS['success'].set_volume(0.3)
SOUNDS['error'].set_volume(0.5)
SOUNDS['notification'].set_volume(0.2)
SOUNDS['callout'].set_volume(0.4)

def play_success_sound():
    SOUNDS['success'].play()

def play_error_sound():
    SOUNDS['error'].play()

def play_notification_sound():
    SOUNDS['notification'].play()

def play_callout():
    SOUNDS['callout'].play()
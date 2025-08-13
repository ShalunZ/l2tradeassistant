# utils/sound.py
import pygame
import os
from config import resource_path

# Инициализация pygame mixer
pygame.mixer.init()

volume = 0.5

# Загрузка звуков
SOUNDS = {
    'success': pygame.mixer.Sound(resource_path('data/sounds/agree.wav')),
    'error': pygame.mixer.Sound(resource_path('data/sounds/angry.wav')),
    'notification': pygame.mixer.Sound(resource_path('data/sounds/wonder.wav')),
    'callout': pygame.mixer.Sound(resource_path('data/sounds/callout.wav'))
}


# Установка громкости (0.0 до 1.0)
SOUNDS['success'].set_volume(volume)
SOUNDS['error'].set_volume(volume)
SOUNDS['notification'].set_volume(volume)
SOUNDS['callout'].set_volume(volume)

def play_success_sound():
    SOUNDS['success'].play()

def play_error_sound():
    SOUNDS['error'].play()

def play_notification_sound():
    SOUNDS['notification'].play()

def play_callout():
    SOUNDS['callout'].play()


def set_sounds_volume(new : float):
    volume = new

    SOUNDS['success'].set_volume(volume)
    SOUNDS['error'].set_volume(volume)
    SOUNDS['notification'].set_volume(volume)
    SOUNDS['callout'].set_volume(volume)
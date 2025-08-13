# utils/sound.py
import winsound
import threading
from config import resource_path
from utils.logger import debug_log
def _play_sound_async(wav_path):
    winsound.PlaySound(wav_path, winsound.SND_FILENAME)

def play_success_sound():
    threading.Thread(target=_play_sound_async, args=(resource_path('data/sounds/agree.wav'),), daemon=True).start()

def play_error_sound():
    threading.Thread(target=_play_sound_async, args=(resource_path('data/sounds/angry.wav'),), daemon=True).start()

def play_notification_sound():
    threading.Thread(target=_play_sound_async, args=(resource_path('data/sounds/wonder.wav'),), daemon=True).start()

def play_callout():
    threading.Thread(target=_play_sound_async, args=(resource_path('data/sounds/callout.wav'),), daemon=True).start()
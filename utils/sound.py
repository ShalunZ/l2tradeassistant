# utils/sound.py
import winsound

def play_success_sound():
    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)

def play_error_sound():
    winsound.PlaySound("SystemHand", winsound.SND_ALIAS)

def play_notification_sound():
    winsound.PlaySound("SystemNotify", winsound.SND_ALIAS)

def play_question_sound():
    winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS)

def play_loud_sound():
    winsound.MessageBeep(winsound.MB_ICONHAND)
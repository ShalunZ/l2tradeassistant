# utils/sound.py
import winsound

# 🔊 Системные звуки (асинхронные)
def play_success_sound():
    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)

def play_error_sound():
    winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)

def play_notification_sound():
    winsound.PlaySound("SystemNotify", winsound.SND_ALIAS | winsound.SND_ASYNC)

def play_question_sound():
    winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS | winsound.SND_ASYNC)

def play_loud_sound():
    winsound.MessageBeep(winsound.MB_ICONHAND)

# 🔔 Простые Beep-сигналы
def beep_short():
    winsound.Beep(800, 150)  # короткий писк

def beep_long():
    winsound.Beep(600, 500)  # длинный писк

def beep_high():
    winsound.Beep(1000, 200)  # высокий писк

def beep_low():
    winsound.Beep(400, 300)  # низкий писк
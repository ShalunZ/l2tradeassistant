# utils/tray.py
import pystray
from PIL import Image
from config import resource_path
from utils.sound import *

# Глобальные переменные
tray_icon = None
lang = "rus"  # Текущий язык: "rus" или "eng"

# Словарь локализации
_ = {
    "rus": {
        "help": "Помощь",
        "change_lang": "Change language",
        "exit": "Выход",
        "tooltip_title": "📌 L2 Trade Tooltip v1.1.1",
        "help_msg": (
            "🔹 Зажмите F + наведите на предмет \n"
            "🔹 Ctrl+P — перезагрузить приложение\n"
            "🔹 Ctrl+Q — безопасный выход\n"
        ),
        "lang_set": "Язык изменён на Русский",
        "tray_title": "L2 Trade Market Analyzer"
    },
    "eng": {
        "help": "Help",
        "change_lang": "Сменить язык",
        "exit": "Exit",
        "tooltip_title": "📌 L2 Trade Tooltip v1.1.1",
        "help_msg": (
            "🔹 Press F + hover over items \n"
            "🔹 Ctrl+P — reload application\n"
            "🔹 Ctrl+Q — exit\n"
        ),
        "lang_set": "Language changed to English",
        "tray_title": "L2 Trade Market Analyzer"
    }
}


def toggle_language(icon):
    """Переключает язык и обновляет меню"""
    global lang
    lang = "eng" if lang == "rus" else "rus"
    update_menu(icon)
    # Показываем уведомление о смене языка
    icon.notify(_[lang]["lang_set"], "Language")


def update_menu(icon):
    """Обновляет меню с учётом текущего языка"""
    icon.menu = pystray.Menu(
        pystray.MenuItem(
            _[lang]["help"],
            lambda icon, item: show_help()
        ),
        pystray.MenuItem(
            _[lang]["change_lang"],
            lambda icon, item: toggle_language(icon)
        ),
        pystray.MenuItem(
            _[lang]["exit"],
            lambda icon, item: icon.stop()  # Остановит иконку, дальше — on_exit_callback
        )
    )
    icon.title = _[lang]["tray_title"]  # Можно обновить заголовок
    icon.update_menu()


def create_tray_icon(on_exit_callback):
    """
    Создаёт иконку в трее.
    """
    global tray_icon

    # Загружаем иконку
    try:
        icon_path = resource_path("data/img/icon.ico")
        image = Image.open(icon_path)
    except Exception as e:
        print(f"❌ Не удалось загрузить иконку: {e}")
        image = Image.new('RGB', (16, 16), 'gray')

    # Создаём меню
    menu = pystray.Menu(
        pystray.MenuItem(
            _[lang]["help"],
            lambda icon, item: show_help()
        ),
        pystray.MenuItem(
            _[lang]["change_lang"],
            lambda icon, item: toggle_language(icon)
        ),
        pystray.MenuItem(
            _[lang]["exit"],
            lambda icon, item: on_exit_callback()
        )
    )

    tray_icon = pystray.Icon(
        name="l2tradebot",
        icon=image,
        title=_[lang]["tray_title"],
        menu=menu
    )

    # Показываем уведомление при запуске
    tray_icon.run_detached()
    tray_icon.notify("Приложение запущено и свернуто в трей.\nНажмите F для анализа.", "L2 Trade Tooltip")
    return tray_icon


def show_help():
    """Показывает окно помощи"""
    tray_icon.notify(_[lang]["help_msg"], _[lang]["tooltip_title"])
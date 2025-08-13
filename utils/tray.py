# utils/tray.py
import pystray
from PIL import Image
import webbrowser,time
import locale
from config import resource_path
from utils.logger import debug_log

# Глобальные переменные
tray_icon = None
lang = "rus"  # Текущий язык: "rus" или "eng"


# Список языков и регионов СНГ
CIS_LANGUAGES = {
    'ru',    # Русский
    'ru_RU', 'ru_UA', 'ru_KZ', 'ru_BY', 'ru_MD',  # Россия, Украина, Казахстан, Беларусь, Молдова
    'uk', 'uk_UA',  # Украинский
    'be', 'be_BY',  # Белорусский
    'kk', 'kk_KZ',  # Казахский
    'hy', 'hy_AM',  # Армянский
    'az', 'az_AZ',  # Азербайджанский
    'uz', 'uz_UZ',  # Узбекский
    'ky', 'ky_KG',  # Киргизский
    'tg', 'tg_TJ'   # Таджикский
}

# Попробуем определить язык системы
try:
    system_locale = locale.getdefaultlocale()[0]  # Например: 'ru_RU', 'en_US'
    if system_locale:
        # Приводим к нижнему регистру
        lang_tag = system_locale.lower()
        if lang_tag in CIS_LANGUAGES:
            lang = "rus"
except Exception as e:
    debug_log(f"⚠️ Не удалось определить язык системы: {e}")
    lang = "eng"  # По умолчанию

debug_log(f"🌍 Язык интерфейса: {'Русский' if lang == 'rus' else 'English'} (локаль: {system_locale})")



# Словарь локализации
_ = {
    "rus": {
        "help": "Помощь",
        "change_lang": "Сменить язык",
        "donate": "Поддержать проект",
        "exit": "Выход",
        "tooltip_title": "📌 L2 Trade Tooltip v1.1.1",
        "help_msg": (
            "🔹 Зажмите F + наведите на предмет \n"
            "🔹 Ctrl+P — перезагрузить приложение\n"
            "🔹 Ctrl+Q — безопасный выход\n"
            "🔹 Приложение свернуто в трей\n"
        ),
        "lang_set": "Язык изменён на Русский",
        "donate_msg": "Спасибо за поддержку проекта!",
        "tray_title": "L2 Trade Market Analyzer",
    },
    "eng": {
        "help": "Help",
        "change_lang": "Change language",
        "donate": "Support project",
        "exit": "Exit",
        "tooltip_title": "📌 L2 Trade Tooltip v1.1.1",
        "help_msg": (
            "🔹 Press F + hover over items \n"
            "🔹 Ctrl+P — reload application\n"
            "🔹 Ctrl+Q — exit\n"
            "🔹 The application is minimized to the tray\n"
        ),
        "lang_set": "Language changed to English",
        "donate_msg": "Thank you for supporting the project!",
        "tray_title": "L2 Trade Market Analyzer",
    }
}

# 🔗 Ссылка для поддержки (можно заменить на Patreon, Boosty, PayPal и т.д.)
DONATE_URL = "https://www.donationalerts.com/r/atblazer"  # ← Замени на свою ссылку


def open_donate_link(icon, item):
    """Открывает ссылку для поддержки"""
    debug_log("💡 Пункт 'Поддержать' выбран")
    webbrowser.open(DONATE_URL)
    # Показываем уведомление
    icon.notify(_[lang]["donate_msg"], "L2 Trade Tooltip")


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
            _[lang]["donate"],
            lambda icon, item: open_donate_link(icon, item)
        ),
        pystray.MenuItem(
            _[lang]["exit"],
            lambda icon, item: icon.stop()
        )
    )
    icon.title = _[lang]["tray_title"]
    icon.update_menu()


def create_tray_icon(on_exit_callback):
    global tray_icon
    try:
        icon_path = resource_path("data/img/icon.ico")
        image = Image.open(icon_path)
    except Exception as e:
        debug_log(f"❌ Не удалось загрузить иконку: {e}")
        image = Image.new('RGB', (16, 16), 'gray')

    menu = pystray.Menu(
        pystray.MenuItem(_[lang]["help"], lambda icon, item: show_help()),
        pystray.MenuItem(_[lang]["change_lang"], lambda icon, item: toggle_language(icon)),
        pystray.MenuItem(_[lang]["donate"], lambda icon, item: open_donate_link(icon, item)),
        pystray.MenuItem(_[lang]["exit"], lambda icon, item: on_exit_callback())
    )

    tray_icon = pystray.Icon(
        name="l2tradebot",
        icon=image,
        title=_[lang]["tray_title"],
        menu=menu
    )

    # Запускаем в фоне
    tray_icon.run_detached()
    time.sleep(0.1)
    tray_icon.notify(_[lang]["help_msg"], "L2 Trade Tooltip")
    return tray_icon


def show_help():
    """Показывает окно помощи"""
    tray_icon.notify(_[lang]["help_msg"], _[lang]["tooltip_title"])

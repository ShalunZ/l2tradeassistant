# utils/splash.py
import tkinter as tk
from PIL import Image, ImageTk, ImageChops
import os
from config import resource_path
from utils.logger import debug_log
class SplashScreen:
    def __init__(self):
        self.root = tk.Toplevel()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")  # Фон под изображением
        self.root.wm_attributes("-transparentcolor", "black")  # Указывает, что "чёрный" станет прозрачным

        # Загружаем PNG с альфа-каналом
        try:
            img_path = resource_path("data/img/loading1.png")
            original = Image.open(img_path).convert("RGBA")
        except Exception as e:
            print(f"❌ Ошибка загрузки splash-экрана: {e}")
            self.root.destroy()
            return

        # Укажи, какого цвета должен быть фон (например, чёрный)
        background_color = (0, 0, 0)  # RGB для чёрного
        # Или (18, 18, 18) для тёмно-серого и т.п.

        # Заменяем прозрачные пиксели на фоновый цвет
        bg = Image.new("RGBA", original.size, background_color + (255,))
        # Накладываем изображение на фон
        composite = Image.alpha_composite(bg, original)
        # Конвертируем в режим, поддерживаемый Tkinter
        photo = ImageTk.PhotoImage(composite.convert("RGB"))

        # Отображаем
        label = tk.Label(self.root, image=photo, bg="black")
        label.image = photo
        label.pack()

        # Центрируем
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")

        # Закрытие
        self.root.after(2000, self.destroy)

    def destroy(self):
        self.root.destroy()
# utils/tray.py (опционально)
import pystray
from PIL import Image

def create_tray_icon():
    img = Image.open("data/img/icon.ico")  # Иконка 16x16
    icon = pystray.Icon("l2tradebot", img, "L2 Trade Tooltip", menu=pystray.Menu(
        pystray.MenuItem("Выход", lambda icon, item: icon.stop())
        #,pystray.MenuItem("TEST",lambda icon,item: test())
    ))
    icon.run()


def test():
    print("MEOWMOEW")
#!/usr/bin/env python3
import sys
import os
from . import gui
from PyQt5.QtWidgets import QApplication


pkg_dir, _ = os.path.split(__file__)

# clear_screen
if sys.platform in ["linux","linux2","darwin"]:
    os.system('clear')
elif sys.platform == "win32":
    os.system('cls')

class ANS_GUI(gui.MainWindow):
    def __init__(self):
        super().__init__()
        gui.btn_close.clicked.connect(lambda: self.close())
        gui.btn_minimize.clicked.connect(lambda: self.showMinimized())
        gui.btn_menu.clicked.connect(lambda: gui.body_menu.setStyleSheet("max-width: 60px"))

def main():
    app = QApplication(sys.argv)
    win = ANS_GUI()
    win.show()
    app.exec_()

if __name__ == "__main__":
    main(**vars(args))

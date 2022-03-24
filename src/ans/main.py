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

def main():
    app = QApplication(sys.argv)
    win = gui.MainWindow()
    win.show()
    app.exec_()

if __name__ == "__main__":
    main(**vars(args))

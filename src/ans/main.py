#!/usr/bin/env python3
import sys
import os
from . import gui
from . import config
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



def main():
    # app = QApplication(sys.argv)
    # win = ANS_GUI()
    # win.show()
    # sys.exit(app.exec_())
    # app.exec_()
    inp = config.read_config('ans_test.conf')
    if inp:
        print(inp)
    else:
        print("False")

if __name__ == "__main__":
    main(**vars(args))

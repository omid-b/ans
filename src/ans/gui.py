import os
import sys 

from PyQt5.QtCore import (
    Qt
)

from PyQt5.QtGui import QPixmap

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QFrame,
    QPushButton,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)

pkg_dir, _ = os.path.split(__file__)
images_dir = os.path.join(pkg_dir,"data","images")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)

        #### HEADER ####
        # header: left
        header_left = QFrame()
        header_left.setObjectName("header_left")
        lyo_header_left = QHBoxLayout()
        global btn_menu
        btn_menu = QPushButton()
        btn_menu.setObjectName("btn_menu")
        lbl_menu = QLabel("menu")
        lyo_header_left.addWidget(btn_menu)
        lyo_header_left.addWidget(lbl_menu)
        lyo_header_left.setAlignment(Qt.AlignLeft)
        header_left.setLayout(lyo_header_left)

        #header: center
        header_center = QFrame()
        header_center.setObjectName("header_center")
        lyo_header_center = QHBoxLayout()
        btn_logo = QPushButton()
        btn_logo.setEnabled(False)
        btn_logo.setObjectName("btn_logo")
        lyo_header_center.addWidget(btn_logo)
        lyo_header_center.setAlignment(Qt.AlignCenter)
        header_center.setLayout(lyo_header_center)

        # header: right
        header_right = QFrame()
        header_right.setObjectName("header_right")
        lyo_header_right = QHBoxLayout()
        global btn_minimize
        global btn_maximize
        global btn_close
        btn_minimize = QPushButton()
        btn_minimize.setObjectName("btn_minimize")
        btn_maximize = QPushButton()
        btn_maximize.setObjectName("btn_maximize")
        btn_close = QPushButton()
        btn_close.setObjectName("btn_close")
        lyo_header_right.addWidget(btn_minimize)
        lyo_header_right.addWidget(btn_maximize)
        lyo_header_right.addWidget(btn_close)
        lyo_header_right.setAlignment(Qt.AlignRight)
        header_right.setLayout(lyo_header_right)

        # HEADER: LAYOUT
        header = QFrame()
        header.setObjectName("header")
        lyo_header = QHBoxLayout()
        lyo_header.addWidget(header_left)
        lyo_header.addWidget(header_center)
        lyo_header.addWidget(header_right)
        lyo_header.setSpacing(0)
        lyo_header.setContentsMargins(0,0,0,0)
        header.setLayout(lyo_header)

        #### BODY ####
        # body: menu
        body_menu = QFrame()
        body_menu.setObjectName("body_menu")
        menu_top = QFrame()
        menu_top.setObjectName("menu_top")
        menu_bottom = QFrame()
        menu_bottom.setObjectName("menu_bottom")
        global btn_setting
        global btn_download
        global btn_mseed2sac
        global btn_sac2ncf
        global btn_ncf2egf
        global btn_terminal
        btn_setting = QPushButton()
        btn_setting.setObjectName("btn_setting")
        btn_download = QPushButton()
        btn_download.setObjectName("btn_download")
        btn_mseed2sac = QPushButton()
        btn_mseed2sac.setObjectName("btn_mseed2sac")
        btn_sac2ncf = QPushButton()
        btn_sac2ncf.setObjectName("btn_sac2ncf")
        btn_ncf2egf = QPushButton()
        btn_ncf2egf.setObjectName("btn_ncf2egf")
        lbl_setting = QLabel("setting")
        lbl_download = QLabel("download")
        lbl_mseed2sac = QLabel("mseed2sac")
        lbl_sac2ncf = QLabel("sac2ncf")
        lbl_ncf2egf = QLabel("ncf2egf")
        btn_terminal = QPushButton("terminal")
        lbl_terminal = QLabel("terminal")
        lyo_menu_top = QGridLayout()
        lyo_menu_top.addWidget(btn_setting, 0,0)
        lyo_menu_top.addWidget(btn_download, 1,0)
        lyo_menu_top.addWidget(btn_mseed2sac, 2,0)
        lyo_menu_top.addWidget(btn_sac2ncf, 3,0)
        lyo_menu_top.addWidget(btn_ncf2egf, 4,0)
        lyo_menu_top.addWidget(lbl_setting, 0,1)
        lyo_menu_top.addWidget(lbl_download, 1,1)
        lyo_menu_top.addWidget(lbl_mseed2sac, 2,1)
        lyo_menu_top.addWidget(lbl_sac2ncf, 3,1)
        lyo_menu_top.addWidget(lbl_ncf2egf, 4,1)
        lyo_menu_top.setAlignment(Qt.AlignTop)
        lyo_menu_bottom = QHBoxLayout()
        lyo_menu_bottom.addWidget(btn_terminal)
        lyo_menu_bottom.addWidget(lbl_terminal)
        lyo_menu_bottom.setAlignment(Qt.AlignBottom)
        menu_top.setLayout(lyo_menu_top)
        menu_bottom.setLayout(lyo_menu_bottom)
        lyo_body_menu = QVBoxLayout()
        lyo_body_menu.addWidget(menu_top)
        lyo_body_menu.addWidget(menu_bottom)
        lyo_body_menu.setSpacing(0)
        lyo_body_menu.setContentsMargins(0,0,0,0)
        body_menu.setLayout(lyo_body_menu)
        # body: main
        body_main = QFrame()
        body_main.setObjectName("body_main")
        lyo_body_main = QVBoxLayout()
        body_main.setLayout(lyo_body_main)

        # BODY: LAYOUT
        body = QFrame()
        body.setObjectName("body")
        lyo_body = QHBoxLayout()
        lyo_body.addWidget(body_menu)
        lyo_body.addWidget(body_main)
        lyo_body.setSpacing(0)
        lyo_body.setContentsMargins(0,0,0,0)
        body.setLayout(lyo_body)

        #### FOOTER ####
        footer = QFrame()
        footer.setObjectName("footer")

        #### MAIN ####
        lyo_main = QVBoxLayout()
        lyo_main.addWidget(header)
        lyo_main.addWidget(body)
        lyo_main.addWidget(footer)
        lyo_main.setSpacing(0)
        lyo_main.setContentsMargins(0,0,0,0)
        main = QFrame()
        main.setLayout(lyo_main)
        self.setCentralWidget(main)

        #### APPLY BUTTON STYLES ###

        # logo
        icon_logo = os.path.join(images_dir,"ans_logo.svg")
        if sys.platform == "win32":
            icon_logo = icon_logo.replace('\\','/')
        
        # close
        icon_close = os.path.join(images_dir,"close.svg")
        icon_close_hover = os.path.join(images_dir,"close_hover.svg")
        if sys.platform == "win32": # qss doesn't accept '\' in path
            icon_close = icon_close.replace('\\','/')
            icon_close_hover = icon_close_hover.replace('\\','/')

        # maximize
        icon_maximize = os.path.join(images_dir,"maximize.svg")
        icon_maximize_hover = os.path.join(images_dir,"maximize_hover.svg")
        if sys.platform == "win32":
            icon_maximize = icon_maximize.replace('\\','/')
            icon_maximize_hover = icon_maximize_hover.replace('\\','/')

        # minimize
        icon_minimize = os.path.join(images_dir,"minimize.svg")
        icon_minimize_hover = os.path.join(images_dir,"minimize_hover.svg")
        if sys.platform == "win32":
            icon_minimize = icon_minimize.replace('\\','/')
            icon_minimize_hover = icon_minimize_hover.replace('\\','/')

        # menu
        icon_menu = os.path.join(images_dir,"menu.svg")
        icon_menu_hover = os.path.join(images_dir,"menu_hover.svg")
        if sys.platform == "win32":
            icon_menu = icon_menu.replace('\\','/')
            icon_menu_hover = icon_menu_hover.replace('\\','/')
        
        # setting
        icon_setting = os.path.join(images_dir,"setting.svg")
        icon_setting_hover = os.path.join(images_dir,"setting_hover.svg")
        if sys.platform == "win32":
            icon_setting = icon_setting.replace('\\','/')
            icon_setting_hover = icon_setting_hover.replace('\\','/')
        
        # download            
        icon_download = os.path.join(images_dir,"download.svg")
        icon_download_hover = os.path.join(images_dir,"download_hover.svg")
        if sys.platform == "win32":
            icon_download = icon_download.replace('\\','/')
            icon_download_hover = icon_download_hover.replace('\\','/')
        
        # mseed2sac
        icon_mseed2sac = os.path.join(images_dir,"mseed2sac.svg")
        icon_mseed2sac_hover = os.path.join(images_dir,"mseed2sac_hover.svg")
        if sys.platform == "win32":
            icon_mseed2sac = icon_mseed2sac.replace('\\','/')
            icon_mseed2sac_hover = icon_mseed2sac_hover.replace('\\','/')
        
        # sac2ncf
        icon_sac2ncf = os.path.join(images_dir,"sac2ncf.svg")
        icon_sac2ncf_hover = os.path.join(images_dir,"sac2ncf_hover.svg")
        if sys.platform == "win32":
            icon_sac2ncf = icon_sac2ncf.replace('\\','/')
            icon_sac2ncf_hover = icon_sac2ncf_hover.replace('\\','/')
        
        # ncf2egf
        icon_ncf2egf = os.path.join(images_dir,"ncf2egf.svg")
        icon_ncf2egf_hover = os.path.join(images_dir,"ncf2egf_hover.svg")
        if sys.platform == "win32":
            icon_ncf2egf = icon_ncf2egf.replace('\\','/')
            icon_ncf2egf_hover = icon_ncf2egf_hover.replace('\\','/')

        self.set_btn_qss(btn_logo, "btn_logo", 50, icon_logo, icon_logo)
        self.set_btn_qss(btn_close, "btn_close", 20, icon_close, icon_close_hover)
        self.set_btn_qss(btn_maximize, "btn_maximize", 20, icon_maximize, icon_maximize_hover)
        self.set_btn_qss(btn_minimize, "btn_minimize", 20, icon_minimize, icon_minimize_hover)
        self.set_btn_qss(btn_menu, "btn_menu", 40, icon_menu, icon_menu_hover)
        self.set_btn_qss(btn_setting, "btn_setting", 40, icon_setting, icon_setting_hover)
        self.set_btn_qss(btn_download, "btn_download", 40, icon_download, icon_download_hover)
        self.set_btn_qss(btn_mseed2sac, "btn_mseed2sac", 40, icon_mseed2sac, icon_mseed2sac_hover)
        self.set_btn_qss(btn_sac2ncf, "btn_sac2ncf", 40, icon_sac2ncf, icon_sac2ncf_hover)
        self.set_btn_qss(btn_ncf2egf, "btn_ncf2egf", 40, icon_ncf2egf, icon_ncf2egf_hover)

        # load external stylesheet file
        with open(os.path.join(pkg_dir,'gui.qss')) as qss:
            qss = qss.read()
            if sys.platform == 'darwin':
                qss = qss + "QMainWindow{font-family: 'Arial'; font-size: 11pt;}"
            else:
                qss = qss + "QMainWindow{font-family: 'Arial'; font-size: 14pt;}"

        self.setStyleSheet(qss)

    def set_btn_qss(self, btn_obj, btn_obj_name, btn_size, icon_file, icon_hover_file):
        qss_code = '''
            #%s {
                min-width: %dpx;
                max-width: %dpx;
                min-height: %dpx;
                max-height: %dpx;
                border: none;
                image: url(%s);
            }

            #%s:hover {
                image: url(%s);
            }

            #%s:pressed {
                border: 2px solid #DDDDF9;
            }
        ''' %(btn_obj_name, btn_size, btn_size, btn_size, btn_size,\
              icon_file, btn_obj_name, icon_hover_file, btn_obj_name)
        btn_obj.setStyleSheet(qss_code)

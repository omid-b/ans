
import os
import sys 

from PyQt5.QtCore import (
    Qt,
    QRect,
    QPoint,
    QEasingCurve,
    QPropertyAnimation,
    pyqtProperty,
)

from PyQt5.QtGui import (
    QPixmap,
    QColor,
    QIcon,
    QPainter,
)

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QFrame,
    QPushButton,
    QLabel,
    QLineEdit,
    QScrollArea,
    QStackedWidget,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)

pkg_dir, _ = os.path.split(__file__)
images_dir = os.path.join(pkg_dir,"data","images")

class MyCheckBox(QCheckBox):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("spacing: 200px;")
        self.setFixedSize(30,18)
        self.setCursor(Qt.PointingHandCursor)
        self.bg_color = '#aaa'
        self.circle_color = '#fff'
        self.active_color = '#299408'
        # for animation
        self._circle_position = 2
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Linear)
        self.animation.setDuration(100)
        self.stateChanged.connect(self.startTransition)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def get_circle_position(self):
        return self._circle_position

    def set_circle_position(self, pos):
        self._circle_position = pos
        self.update()

    circle_position = pyqtProperty(float, get_circle_position, set_circle_position)
    
    def startTransition(self, value):
        self.animation.stop()
        if value:
            self.animation.setEndValue(self.width() - self.height() + 2)
        else:
            self.animation.setEndValue(2)
        self.animation.start()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # draw background rectangle
        rect = QRect(0, 0, self.width(), self.height())
        
        # draw circle
        if  self.isChecked():
            painter.setBrush(QColor(self.active_color))
            painter.drawRoundedRect(0, 0, rect.width(), rect.height(),
                                    rect.height() / 2, rect.height() / 2)
            painter.setBrush(QColor(self.circle_color))
            # painter.drawEllipse(self.width() - self.height() + 2, 2,
            #                     self.height() - 4, self.height() - 4)
            painter.drawEllipse(self._circle_position, 2,
                                self.height() - 4, self.height() - 4)
        else:
            painter.setBrush(QColor(self.bg_color))
            painter.drawRoundedRect(0, 0, rect.width(), rect.height(),
                                    rect.height() / 2, rect.height() / 2)
            painter.setBrush(QColor(self.circle_color))
            painter.drawEllipse(self._circle_position, 2,
                                self.height() - 4, self.height() - 4)

        painter.end()




















class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        app_icon = QIcon()
        app_icon.addFile(os.path.join(images_dir,'ans_logo.svg'))
        self.setWindowIcon(app_icon)

        # global vars
        global btn_menu
        global btn_minimize
        global btn_maximize
        global btn_close
        global btn_setting
        global btn_download
        global btn_mseed2sac
        global btn_sac2ncf
        global btn_ncf2egf
        global btn_terminal
        global btn_save
        global btn_discard
        global btn_revert
        global body_menu
        global body_main

        # load external stylesheet file
        with open(os.path.join(pkg_dir,'gui.qss')) as qss:
            qss = qss.read()
            if sys.platform == 'darwin':
                qss = "\nQFrame { font-family: 'Arial';\n font-size: 14pt;}\n" + qss
            else:
                qss = "\nQFrame { font-family: 'Arial';\n font-size: 11pt;}\n" + qss
        self.setStyleSheet(qss)

        #### HEADER ####
        # header: left
        header_left = QFrame()
        header_left.setObjectName("header_left")
        lyo_header_left = QHBoxLayout()
        btn_menu = QPushButton()
        btn_menu.setObjectName("btn_menu")
        lbl_menu = QLabel("Menu")
        lyo_header_left.addWidget(btn_menu)
        lyo_header_left.addWidget(lbl_menu)
        lyo_header_left.setAlignment(Qt.AlignLeft)
        lyo_header_left.setSpacing(10)
        lyo_header_left.setContentsMargins(10,10,0,10)
        header_left.setLayout(lyo_header_left)

        #header: center
        header_center = QFrame()
        header_center.setObjectName("header_center")
        lyo_header_center = QHBoxLayout()
        btn_logo = QPushButton()
        btn_logo.setEnabled(False)
        btn_logo.setObjectName("btn_logo")
        lbl_title = QLabel("Ambient Noise Seismology (ANS)")
        lbl_title.setObjectName("lbl_title")
        lyo_header_center.addWidget(btn_logo)
        lyo_header_center.addWidget(lbl_title)
        lyo_header_center.setAlignment(Qt.AlignCenter)
        lyo_header_center.setSpacing(5)
        lyo_header_center.setContentsMargins(10,10,0,10)
        header_center.setLayout(lyo_header_center)

        # header: right
        header_right = QFrame()
        header_right.setObjectName("header_right")
        lyo_header_right = QHBoxLayout()
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
        # body_menu.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,\
        #                                     QSizePolicy.Preferred))
        menu_top = QFrame()
        menu_top.setObjectName("menu_top")
        menu_bottom = QFrame()
        menu_bottom.setObjectName("menu_bottom")
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
        lbl_setting = QLabel("Setting")
        lbl_download = QLabel("Data Acquisition")
        lbl_mseed2sac = QLabel("Mseed to SAC")
        lbl_sac2ncf = QLabel("SAC to NCF")
        lbl_ncf2egf = QLabel("NCF to EGF")
        btn_terminal = QPushButton()
        btn_terminal.setObjectName("btn_terminal")
        lbl_terminal = QLabel("Show/Hide\nTerminal")
        btn_about = QPushButton()
        btn_about.setObjectName("btn_about")
        lbl_about = QLabel("About")
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
        lyo_menu_top.setSpacing(10)
        lyo_menu_top.setContentsMargins(10,10,10,0)
        lyo_menu_bottom = QGridLayout()
        lyo_menu_bottom.addWidget(btn_terminal, 0,0)
        lyo_menu_bottom.addWidget(lbl_terminal, 0,1)
        lyo_menu_bottom.addWidget(btn_about, 1,0)
        lyo_menu_bottom.addWidget(lbl_about, 1,1)
        lyo_menu_bottom.setAlignment(Qt.AlignBottom)
        lyo_menu_bottom.setSpacing(10)
        lyo_menu_bottom.setContentsMargins(10,10,0,10)
        menu_top.setLayout(lyo_menu_top)
        menu_bottom.setLayout(lyo_menu_bottom)
        lyo_body_menu = QVBoxLayout()
        lyo_body_menu.addWidget(menu_top)
        lyo_body_menu.addWidget(menu_bottom)
        lyo_body_menu.setSpacing(0)
        lyo_body_menu.setContentsMargins(0,0,0,0)
        body_menu.setLayout(lyo_body_menu)

        # body: main
        body_main = QStackedWidget()
        body_main.setObjectName("body_main")
        body_main.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,\
                                            QSizePolicy.MinimumExpanding))
        setting = QWidget()
        download = QWidget()
        mseed2sac = QWidget()
        sac2ncf = QWidget()
        ncf2egf = QWidget()
        lyo_setting = QVBoxLayout()
        lyo_download = QVBoxLayout()
        lyo_mseed2sac = QVBoxLayout()
        lyo_sac2ncf = QVBoxLayout()
        lyo_ncf2egf = QVBoxLayout()

        chb = MyCheckBox()
        lyo_setting.addWidget(chb, Qt.AlignCenter, Qt.AlignCenter)
        lyo_download.addWidget(QCheckBox("Widget: download"), Qt.AlignCenter, Qt.AlignCenter)
        lyo_mseed2sac.addWidget(QLabel("Widget: mseed2sac"), Qt.AlignCenter, Qt.AlignCenter)
        lyo_sac2ncf.addWidget(QLabel("Widget: sac2ncf"), Qt.AlignCenter, Qt.AlignCenter)
        lyo_ncf2egf.addWidget(QLabel("Widget: ncf2egf"), Qt.AlignCenter, Qt.AlignCenter)

        setting.setLayout(lyo_setting)
        download.setLayout(lyo_download)
        mseed2sac.setLayout(lyo_mseed2sac)
        sac2ncf.setLayout(lyo_sac2ncf)
        ncf2egf.setLayout(lyo_ncf2egf)

        body_main.addWidget(setting)
        body_main.addWidget(download)
        body_main.addWidget(mseed2sac)
        body_main.addWidget(sac2ncf)
        body_main.addWidget(ncf2egf)

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
        footer_left = QFrame()
        footer_left.setObjectName("footer_left")
        footer_right = QFrame()
        footer_right.setObjectName("footer_right")
        lyo_footer = QHBoxLayout()

        # footer_left
        lyo_footer_left = QHBoxLayout()
        lbl_status = QLabel('Status info here ...')
        lbl_status.setObjectName("lbl_status")
        lyo_footer_left.addWidget(lbl_status)
        lyo_footer_left.setAlignment(Qt.AlignLeft)
        footer_left.setLayout(lyo_footer_left)

        # footer_right
        lyo_footer_right = QHBoxLayout()
        btn_save = QPushButton()
        btn_save.setObjectName("btn_save")
        btn_discard = QPushButton()
        btn_discard.setObjectName("btn_discard")
        btn_revert = QPushButton()
        btn_revert.setObjectName("btn_revert")
        lyo_footer_right.addWidget(btn_revert)
        lyo_footer_right.addWidget(btn_discard)
        lyo_footer_right.addWidget(btn_save)
        lyo_footer_right.setAlignment(Qt.AlignRight)
        footer_right.setLayout(lyo_footer_right)
        lyo_footer.addWidget(footer_left)
        lyo_footer.addWidget(footer_right)
        lyo_footer.setSpacing(0)
        lyo_footer.setContentsMargins(0,0,0,0)
        footer.setLayout(lyo_footer)

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

        # terminal
        icon_terminal = os.path.join(images_dir,"terminal.svg")
        icon_terminal_hover = os.path.join(images_dir,"terminal_hover.svg")
        if sys.platform == "win32":
            icon_terminal = icon_terminal.replace('\\','/')
            icon_terminal_hover = icon_terminal_hover.replace('\\','/')

        # about
        icon_about = os.path.join(images_dir,"about.svg")
        icon_about_hover = os.path.join(images_dir,"about_hover.svg")
        if sys.platform == "win32":
            icon_about = icon_about.replace('\\','/')
            icon_about_hover = icon_about_hover.replace('\\','/')

        # save
        icon_save = os.path.join(images_dir,"save.svg")
        icon_save_hover = os.path.join(images_dir,"save_hover.svg")
        if sys.platform == "win32":
            icon_save = icon_save.replace('\\','/')
            icon_save_hover = icon_save_hover.replace('\\','/')

        # discard
        icon_discard = os.path.join(images_dir,"discard.svg")
        icon_discard_hover = os.path.join(images_dir,"discard_hover.svg")
        if sys.platform == "win32":
            icon_discard = icon_discard.replace('\\','/')
            icon_discard_hover = icon_discard_hover.replace('\\','/')

        # revert
        icon_revert = os.path.join(images_dir,"revert.svg")
        icon_revert_hover = os.path.join(images_dir,"revert_hover.svg")
        if sys.platform == "win32":
            icon_revert = icon_revert.replace('\\','/')
            icon_revert_hover = icon_revert_hover.replace('\\','/')

        self.set_btn_qss(btn_logo, "btn_logo", (50, 50), icon_logo, icon_logo, 3,'#DDDDF9')
        self.set_btn_qss(btn_close, "btn_close", (20,20), icon_close, icon_close_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_maximize, "btn_maximize", (20,20), icon_maximize, icon_maximize_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_minimize, "btn_minimize", (20,20), icon_minimize, icon_minimize_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_menu, "btn_menu", (40,40), icon_menu, icon_menu_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_setting, "btn_setting", (40,40), icon_setting, icon_setting_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_download, "btn_download", (40,40), icon_download, icon_download_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_mseed2sac, "btn_mseed2sac", (40,40), icon_mseed2sac, icon_mseed2sac_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_sac2ncf, "btn_sac2ncf", (40,40), icon_sac2ncf, icon_sac2ncf_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_ncf2egf, "btn_ncf2egf", (40,40), icon_ncf2egf, icon_ncf2egf_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_terminal, "btn_terminal", (40,40), icon_terminal, icon_terminal_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_about, "btn_about", (40,40), icon_about, icon_about_hover, 3,'#DDDDF9')
        self.set_btn_qss(btn_revert, "btn_revert", (167,35), icon_revert, icon_revert_hover,2,'#DDDDF9')
        self.set_btn_qss(btn_discard, "btn_discard", (167,35), icon_discard, icon_discard_hover,2,'#DDDDF9')
        self.set_btn_qss(btn_save, "btn_save", (167,35), icon_save, icon_save_hover,2,'#DDDDF9')

        # remove title bar
        # self.setWindowFlags(Qt.FramelessWindowHint)

        # self.setAttribute(Qt.WA_TranslucentBackground)

        # self.shadow = QGraphicsDropShadowEffect(self)
        # self.shadow.setBlurRadius(50)
        # self.shadow.setXOffset(0)
        # self.shadow.setYOffset(0)
        # self.shadow.setColor(QColor(256,0,0))

        # self.setGraphicsEffect(self.shadow)


    def set_btn_qss(self, btn_obj, btn_obj_name,\
                    btn_size, icon_file, icon_hover_file,\
                    icon_clicked_border_size, icon_clicked_border_color):
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
                border: %dpx solid %s;
            }
        ''' %(btn_obj_name, btn_size[0], btn_size[0], btn_size[1], btn_size[1],\
              icon_file, btn_obj_name, icon_hover_file, btn_obj_name,\
              icon_clicked_border_size, icon_clicked_border_color)
        btn_obj.setStyleSheet(qss_code)


import os
import sys 
import re

from PyQt5.QtCore import (
    Qt,
    QRect,
    QPoint,
    QEasingCurve,
    QPropertyAnimation,
    pyqtProperty,
    QCoreApplication,
    QSize,
)

from PyQt5.QtGui import (
    QColor,
    QIcon,
    QPainter,
    QPalette,
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
    QFileDialog,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)


pkg_dir, _ = os.path.split(__file__)
images_dir = os.path.join(pkg_dir,"data","images")

class MyLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()

    def isfile(self): # is an existing file
        f = self.text()
        if os.path.isfile(f) or f == '':
            self.setStyleSheet("color: black")
            if os.path.isfile(f):
                return True
        else:
            self.setStyleSheet("color: red")
            return False

    def isdir(self): # is an existing directory
        d = self.text()
        if os.path.isdir(d) or d == '':
            self.setStyleSheet("color: black")
            if os.path.isdir(d):
                return True
        else:
            self.setStyleSheet("color: red")
            return False

    def isdate(self): # is a date value: 'YYYY-MM-DD'
        text = self.text()
        rexpr = re.compile("^[1-2][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]$")
        if rexpr.match(text) or text == '':
            self.setStyleSheet("color: black")
            if rexpr.match(text):
                return True
        else:
            self.setStyleSheet("color: red")
            return False

    def islat(self): # is a latitude value
        text = self.text()
        try:
            val = float(text)
            if val >= -90 and val <= 90:
                self.setStyleSheet("color: black")
                return True
            else:
                self.setStyleSheet("color: red")
                return False
        except ValueError:
            if len(text):
                self.setStyleSheet("color: red")
            else:
                self.setStyleSheet("color: black")
            return False

    def islon(self): # is a longitude value
        text = self.text()
        try:
            val = float(text)
            if val >= -180 and val <= 180:
                self.setStyleSheet("color: black")
                return True
            else:
                self.setStyleSheet("color: red")
                return False
        except ValueError:
            if len(text):
                self.setStyleSheet("color: red")
            else:
                self.setStyleSheet("color: black")
            return False

    def isposint(self): # is positive integer
        text = self.text()
        try:
            val = int(text)
            if val > 0:
                self.setStyleSheet("color: black")
                return True
            else:
                self.setStyleSheet("color: red")
                return False
        except ValueError:
            if len(text):
                self.setStyleSheet("color: red")
            else:
                self.setStyleSheet("color: black")
            return False


class MyCheckBox(QCheckBox):
    def __init__(self):
        super().__init__()
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




class MyDialog(QPushButton):

    def __init__(self, text='...', type=0, filters='All Files (*)', lineEditObj=None):
        super().__init__()
        # size=[30,23]
        # self.setFixedSize(QSize(size[0], size[1]))
        self.filters = filters
        self.lineEditObj = lineEditObj
        self.setText(text)
        self.setCursor(Qt.PointingHandCursor)
        if type == 1:
            self.clicked.connect(self.select_file)
        elif type == 2:
            self.clicked.connect(self.select_files)
        elif type == 3:
            self.clicked.connect(self.select_directory)
        elif type == 4:
            self.clicked.connect(self.save_file)
        else:
            pass

    def select_file(self):
        ret = ""
        response, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select file",
            directory=os.getcwd(),
            filter=self.filters,
        )
        if self.lineEditObj != None and response != "":
            ret = os.path.abspath(response)
            self.lineEditObj.setText(ret)
        return ret


    def select_files(self):
        ret = []
        response, _ = QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select files",
            directory=os.getcwd(),
            filter=self.filters,
        )
        if self.lineEditObj != None and response != []:
            for f in response:
                ret.append(os.path.abspath(f))
            ret = "; ".join(ret)
            self.lineEditObj.setText(ret)
        return ret


    def select_directory(self):
        ret = ""
        response = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select directory",
            directory=os.getcwd(),
        )
        print(response)
        if self.lineEditObj != None and response != "":
            ret = os.path.abspath(response)
            self.lineEditObj.setText(ret)
        return ret


    def save_file(self):
        ret = ""
        response, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save file name",
            directory=os.getcwd(),
            filter=self.filters,
        )
        if self.lineEditObj != None and response != "":
            ret = os.path.abspath(response)
            self.lineEditObj.setText(ret)
        return ret




class Project_Setting(QWidget):
    def __init__(self):
        super().__init__()
        global le_maindir
        global le_startdate
        global le_enddate
        global le_maxlat
        global le_minlat
        global le_minlon
        global le_maxlon
        global le_sac
        global le_gmt
        global le_perl
        # project general setting (top section)
        # widgets
        lbl_proj = QLabel("Project general setting:")
        lbl_proj.setObjectName("lbl_proj")
        lbl_maindir = QLabel("Main dir:")
        lbl_maindir.setObjectName("lbl_maindir")
        le_maindir = MyLineEdit()
        le_maindir.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_maindir.setObjectName("le_maindir")
        le_maindir.setPlaceholderText("Full path to project main directory")
        le_maindir.textChanged.connect(le_maindir.isdir)
        browse_maindir = MyDialog(type=3, lineEditObj=le_maindir)
        lbl_startdate = QLabel("Start date:")
        lbl_startdate.setObjectName("lbl_startdate")
        le_startdate = MyLineEdit()
        le_startdate.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_startdate.setAlignment(Qt.AlignCenter)
        le_startdate.setObjectName("le_startdate")
        le_startdate.setPlaceholderText("YYYY-MM-DD")
        le_startdate.textChanged.connect(le_startdate.isdate)
        lbl_enddate = QLabel("End date:")
        lbl_enddate.setObjectName("lbl_enddate")
        le_enddate = MyLineEdit()
        le_enddate.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_enddate.setAlignment(Qt.AlignCenter)
        le_enddate.setObjectName("le_enddate")
        le_enddate.setPlaceholderText("YYYY-MM-DD")
        le_enddate.textChanged.connect(le_enddate.isdate)
        lbl_studyarea = QLabel("Study area boundaries")
        lbl_studyarea.setObjectName("lbl_studyarea")
        le_maxlat = MyLineEdit()
        le_maxlat.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_maxlat.setObjectName("le_maxlat")
        le_maxlat.setAlignment(Qt.AlignCenter)
        le_maxlat.setPlaceholderText("Max Lat (deg)")
        le_maxlat.textChanged.connect(le_maxlat.islat)
        le_minlat = MyLineEdit()
        le_minlat.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_minlat.setObjectName("le_minlat")
        le_minlat.setAlignment(Qt.AlignCenter)
        le_minlat.setPlaceholderText("Min Lat (deg)")
        le_minlat.textChanged.connect(le_minlat.islat)
        le_minlon = MyLineEdit()
        le_minlon.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_minlon.setObjectName("le_minlon")
        le_minlon.setAlignment(Qt.AlignCenter)
        le_minlon.setPlaceholderText("Min Lon (deg)")
        le_minlon.textChanged.connect(le_minlon.islon)
        le_maxlon = MyLineEdit()
        le_maxlon.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_maxlon.setObjectName("le_maxlon")
        le_maxlon.setAlignment(Qt.AlignCenter)
        le_maxlon.setPlaceholderText("Max Lon (deg)")
        le_maxlon.textChanged.connect(le_maxlon.islon)
        btn_showmap = QPushButton("Show map")
        btn_showmap.setObjectName("btn_showmap")
        btn_showmap.setEnabled(True)
        if btn_showmap.isEnabled():
            btn_showmap.setCursor(Qt.PointingHandCursor)
        lbl_depend = QLabel("Program dependencies:")
        lbl_depend.setObjectName("lbl_depend")
        lbl_sac = QLabel("SAC:")
        lbl_sac.setObjectName("lbl_sac")
        le_sac = MyLineEdit()
        le_sac.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_sac.setObjectName("le_sac")
        le_sac.setPlaceholderText("Full path to SAC executable")
        le_sac.textChanged.connect(le_sac.isfile)
        browse_sac = MyDialog(type=1, lineEditObj=le_sac)

        lbl_gmt = QLabel("GMT:")
        lbl_gmt.setObjectName("lbl_gmt")
        le_gmt = MyLineEdit()
        le_gmt.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_gmt.setObjectName("le_gmt")
        le_gmt.setPlaceholderText("Full path to GMT executable") 
        le_gmt.textChanged.connect(le_gmt.isfile)
        browse_gmt = MyDialog(type=1, lineEditObj=le_gmt)

        lbl_perl = QLabel("Perl:")
        lbl_perl.setObjectName("lbl_perl")
        le_perl = MyLineEdit()
        le_perl.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_perl.setObjectName("le_perl")
        le_perl.setPlaceholderText("Full path to the Perl interpreter")
        le_perl.textChanged.connect(le_perl.isfile)
        browse_perl = MyDialog(type=1, lineEditObj=le_perl)

        # Design layouts

        ## Top Left/Right 
        lyo_tl = QGridLayout()
        lyo_tl.addWidget(lbl_maindir,0,0)
        lyo_tl.addWidget(le_maindir,0,1)
        lyo_tl.addWidget(browse_maindir,0,2)
        lyo_tl.addWidget(lbl_startdate,1,0)
        lyo_tl.addWidget(le_startdate,1,1)
        lyo_tl.addWidget(lbl_enddate,2,0)
        lyo_tl.addWidget(le_enddate,2,1)
        lyo_tl.setContentsMargins(0,0,0,0)
        lyo_tl.setVerticalSpacing(10)
        lyo_tl.setHorizontalSpacing(0)

        lyo_tr = QGridLayout()
        lyo_tr.addWidget(le_maxlat,0,1)
        lyo_tr.addWidget(le_minlon,1,0)
        lyo_tr.addWidget(le_maxlon,1,2)
        lyo_tr.addWidget(le_minlat,2,1)
        lyo_tr.addWidget(btn_showmap,3,1)
        lyo_tr.setContentsMargins(0,0,0,0)
        lyo_tr.setVerticalSpacing(10)
        lyo_tr.setHorizontalSpacing(0)

        lyo_top = QGridLayout()
        lyo_top.addWidget(lbl_proj, 0,0,1,3)
        lyo_top.addWidget(lbl_studyarea, 0,3,1,2)
        lyo_top.addLayout(lyo_tl,1,0,1,3)
        lyo_top.addLayout(lyo_tr,1,3,1,2)
        lyo_top.setVerticalSpacing(10)
        lyo_top.setHorizontalSpacing(30)
        lyo_top.setContentsMargins(0,0,0,0)

        ## bottom ##
        lyo_bottom = QGridLayout()
        lyo_bottom.addWidget(lbl_depend,0,0,1,3)
        lyo_bottom.addWidget(lbl_sac,1,0,1,1)
        lyo_bottom.addWidget(le_sac,1,1,1,1)
        lyo_bottom.addWidget(browse_sac,1,2,1,1)
        lyo_bottom.addWidget(lbl_gmt,2,0,1,1)
        lyo_bottom.addWidget(le_gmt,2,1,1,1)
        lyo_bottom.addWidget(browse_gmt,2,2,1,1)
        lyo_bottom.addWidget(lbl_perl,3,0,1,1)
        lyo_bottom.addWidget(le_perl,3,1,1,1)
        lyo_bottom.addWidget(browse_perl,3,2,1,1)
        lyo_bottom.setVerticalSpacing(10)
        lyo_bottom.setHorizontalSpacing(10)
        lyo_bottom.setContentsMargins(0,0,0,0)

        # put together top and bottom layouts
        self.layout = QVBoxLayout()
        self.layout.addLayout(lyo_top)
        self.layout.addLayout(lyo_bottom)
        self.layout.setSpacing(30)
        self.layout.setContentsMargins(60,60,60,60)
        self.setLayout(self.layout)








class Download(QWidget):
    def __init__(self):
        super().__init__()
        global chb_dc_service_iris_edu
        global chb_dc_service_ncedc_org
        global chb_dc_service_scedc_caltech_edu
        global chb_dc_rtserve_beg_utexas_edu
        global chb_dc_eida_bgr_de
        global chb_dc_ws_resif_fr
        global chb_dc_seisrequest_iag_usp_br
        global chb_dc_eida_service_koeri_boun_edu_tr
        global chb_dc_eida_ethz_ch
        global chb_dc_geofon_gfz_potsdam_de
        global chb_dc_ws_icgc_cat
        global chb_dc_eida_ipgp_fr
        global chb_dc_fdsnws_raspberryshakedata_com
        global chb_dc_webservices_ingv_it
        global chb_dc_erde_geophysik_uni_muenchen_de
        global chb_dc_eida_sc3_infp_ro
        global chb_dc_eida_gein_noa_gr
        global chb_dc_www_orfeus_eu_org
        global chb_dc_auspass_edu_au
        global le_stalist
        global le_stameta
        global le_stalocs
        global le_stachns
        global le_timelen
        global chb_obspy
        global chb_fetch
        lbl_datacenters = QLabel("Datacenters:")
        lbl_datacenters.setObjectName("lbl_datacenters")
        chb_dc_service_iris_edu = MyCheckBox()
        lbl_dc_service_iris_edu = QLabel("service.iris.edu")
        chb_dc_service_iris_edu.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_service_iris_edu.setObjectName("chb_dc_service_iris_edu")
        chb_dc_service_ncedc_org = MyCheckBox()
        lbl_dc_service_ncedc_org = QLabel("service.ncedc.org")
        chb_dc_service_ncedc_org.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_service_ncedc_org.setObjectName("chb_dc_service_ncedc_org")
        chb_dc_service_scedc_caltech_edu = MyCheckBox()
        lbl_dc_service_scedc_caltech_edu = QLabel("service.scedc.caltech.edu")
        chb_dc_service_scedc_caltech_edu.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_service_scedc_caltech_edu.setObjectName("chb_dc_service_scedc_caltech_edu")
        chb_dc_rtserve_beg_utexas_edu = MyCheckBox()
        lbl_dc_rtserve_beg_utexas_edu = QLabel("rtserve.beg.utexas.edu")
        chb_dc_rtserve_beg_utexas_edu.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_rtserve_beg_utexas_edu.setObjectName("chb_dc_rtserve_beg_utexas_edu")
        chb_dc_eida_bgr_de = MyCheckBox()
        lbl_dc_eida_bgr_de = QLabel("eida.bgr.de")
        chb_dc_eida_bgr_de.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_eida_bgr_de.setObjectName("chb_dc_eida_bgr_de")
        chb_dc_ws_resif_fr = MyCheckBox()
        lbl_dc_ws_resif_fr = QLabel("ws.resif.fr")
        chb_dc_ws_resif_fr.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_ws_resif_fr.setObjectName("chb_dc_ws_resif_fr")
        chb_dc_seisrequest_iag_usp_br = MyCheckBox()
        lbl_dc_seisrequest_iag_usp_br = QLabel("seisrequest.iag.usp.br")
        chb_dc_seisrequest_iag_usp_br.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_seisrequest_iag_usp_br.setObjectName("chb_dc_seisrequest_iag_usp_br")
        chb_dc_eida_service_koeri_boun_edu_tr = MyCheckBox()
        lbl_dc_eida_service_koeri_boun_edu_tr = QLabel("eida-service.koeri.boun.edu.tr")
        chb_dc_eida_service_koeri_boun_edu_tr.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_eida_service_koeri_boun_edu_tr.setObjectName("chb_dc_eida_service_koeri_boun_edu_tr")
        chb_dc_eida_ethz_ch = MyCheckBox()
        lbl_dc_eida_ethz_ch = QLabel("eida.ethz.ch")
        chb_dc_eida_ethz_ch.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_eida_ethz_ch.setObjectName("chb_dc_eida_ethz_ch")
        chb_dc_geofon_gfz_potsdam_de = MyCheckBox()
        lbl_dc_geofon_gfz_potsdam_de = QLabel("geofon.gfz-potsdam.de")
        chb_dc_geofon_gfz_potsdam_de.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_geofon_gfz_potsdam_de.setObjectName("chb_dc_geofon_gfz_potsdam_de")
        chb_dc_ws_icgc_cat = MyCheckBox()
        lbl_dc_ws_icgc_cat = QLabel("ws.icgc.cat")
        chb_dc_ws_icgc_cat.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_ws_icgc_cat.setObjectName("chb_dc_ws_icgc_cat")
        chb_dc_eida_ipgp_fr = MyCheckBox()
        lbl_dc_eida_ipgp_fr = QLabel("eida.ipgp.fr")
        chb_dc_eida_ipgp_fr.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_eida_ipgp_fr.setObjectName("chb_dc_eida_ipgp_fr")
        chb_dc_fdsnws_raspberryshakedata_com = MyCheckBox()
        lbl_dc_fdsnws_raspberryshakedata_com = QLabel("fdsnws.raspberryshakedata.com")
        chb_dc_fdsnws_raspberryshakedata_com.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_fdsnws_raspberryshakedata_com.setObjectName("chb_dc_fdsnws_raspberryshakedata_com")
        # column 3 widgets
        chb_dc_webservices_ingv_it = MyCheckBox()
        lbl_dc_webservices_ingv_it = QLabel("webservices.ingv.it")
        chb_dc_webservices_ingv_it.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_webservices_ingv_it.setObjectName("chb_dc_webservices_ingv_it")
        chb_dc_erde_geophysik_uni_muenchen_de = MyCheckBox()
        lbl_dc_erde_geophysik_uni_muenchen_de = QLabel("erde.geophysik.uni-muenchen.de")
        chb_dc_erde_geophysik_uni_muenchen_de.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_erde_geophysik_uni_muenchen_de.setObjectName("chb_dc_erde_geophysik_uni_muenchen_de")
        chb_dc_eida_sc3_infp_ro = MyCheckBox()
        lbl_dc_eida_sc3_infp_ro = QLabel("eida-sc3.infp.ro")
        chb_dc_eida_sc3_infp_ro.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_eida_sc3_infp_ro.setObjectName("chb_dc_eida_sc3_infp_ro")
        chb_dc_eida_gein_noa_gr = MyCheckBox()
        lbl_dc_eida_gein_noa_gr = QLabel("eida.gein.noa.gr")
        chb_dc_eida_gein_noa_gr.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_eida_gein_noa_gr.setObjectName("chb_dc_eida_gein_noa_gr")
        chb_dc_www_orfeus_eu_org = MyCheckBox()
        lbl_dc_www_orfeus_eu_org = QLabel("www.orfeus-eu.org")
        chb_dc_www_orfeus_eu_org.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_www_orfeus_eu_org.setObjectName("chb_dc_www_orfeus_eu_org")
        chb_dc_auspass_edu_au = MyCheckBox()
        lbl_dc_auspass_edu_au = QLabel("auspass.edu.au")
        chb_dc_auspass_edu_au.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_dc_auspass_edu_au.setObjectName("chb_dc_auspass_edu_au")
        #### Download setting (bottom panel) ####
        # bottom left
        lbl_dlsetting = QLabel("Download setting:")
        lbl_dlsetting.setObjectName("lbl_dlsetting")
        lbl_stalist = QLabel("Station list file:")
        lbl_stalist.setObjectName("lbl_stalist")
        le_stalist = MyLineEdit()
        le_stalist.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_stalist.setObjectName("le_stalist")
        le_stalist.setPlaceholderText("Full path to station list file")
        le_stalist.textChanged.connect(le_stalist.isfile)
        browse_stalist = MyDialog(type=1, lineEditObj=le_stalist)
        #
        lbl_stameta = QLabel("Station meta files dir:")
        lbl_stameta.setObjectName("lbl_stameta")
        le_stameta = MyLineEdit()
        le_stameta.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_stameta.setObjectName("le_stameta")
        le_stameta.setPlaceholderText("Full path to station meta files directory")
        le_stameta.textChanged.connect(le_stameta.isdir)
        browse_stameta = MyDialog(type=3, lineEditObj=le_stameta)
        #
        lbl_stalocs = QLabel("Station location codes:")
        lbl_stalocs.setObjectName("lbl_stalocs")
        le_stalocs = MyLineEdit()
        le_stalocs.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_stalocs.setObjectName("le_stalocs")
        le_stalocs.setPlaceholderText("Station location codes separated by space")
        #
        lbl_stachns = QLabel("Station channels:")
        lbl_stachns.setObjectName("lbl_stachns")
        le_stachns = MyLineEdit()
        le_stachns.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_stachns.setObjectName("le_stachns")
        le_stachns.setPlaceholderText("Station channels separated by space")
        #
        lbl_timelen = QLabel("Timeseries length (s):")
        lbl_timelen.setObjectName("lbl_timelen")
        le_timelen = MyLineEdit()
        le_timelen.setAttribute(Qt.WA_MacShowFocusRect, 0)
        le_timelen.setObjectName("le_timelen")
        le_timelen.textChanged.connect(le_timelen.isposint)
        le_timelen.setPlaceholderText("Timeseries length in seconds")
        # bottom right
        lbl_dlscripts = QLabel("Download scripts:")
        lbl_dlscripts.setObjectName("lbl_dlscripts")
        chb_obspy = MyCheckBox()
        lbl_obspy = QLabel("ObsPy script")
        chb_obspy.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_obspy.setObjectName("chb_obspy")
        chb_fetch = MyCheckBox()
        lbl_fetch = QLabel("IRIS FetchData Perl script")
        chb_fetch.setAttribute(Qt.WA_MacShowFocusRect, 0)
        chb_fetch.setObjectName("chb_fetch")

        # design layouts
        # top
        lyo_datacenters = QGridLayout()
        lyo_datacenters.addWidget(lbl_datacenters,0,0,1,6)
        lyo_datacenters.addWidget(chb_dc_service_iris_edu, 1,0)
        lyo_datacenters.addWidget(lbl_dc_service_iris_edu, 1,1)
        lyo_datacenters.addWidget(chb_dc_service_ncedc_org, 1,2)
        lyo_datacenters.addWidget(lbl_dc_service_ncedc_org, 1,3)
        lyo_datacenters.addWidget(chb_dc_service_scedc_caltech_edu, 1,4)
        lyo_datacenters.addWidget(lbl_dc_service_scedc_caltech_edu, 1,5)
        lyo_datacenters.addWidget(chb_dc_auspass_edu_au, 2,0)
        lyo_datacenters.addWidget(lbl_dc_auspass_edu_au, 2,1)
        lyo_datacenters.addWidget(chb_dc_eida_bgr_de, 2,2)
        lyo_datacenters.addWidget(lbl_dc_eida_bgr_de, 2,3)
        lyo_datacenters.addWidget(chb_dc_eida_ethz_ch, 2,4)
        lyo_datacenters.addWidget(lbl_dc_eida_ethz_ch, 2,5)
        lyo_datacenters.addWidget(chb_dc_eida_gein_noa_gr, 3,0)
        lyo_datacenters.addWidget(lbl_dc_eida_gein_noa_gr, 3,1)
        lyo_datacenters.addWidget(chb_dc_eida_ipgp_fr, 3,2)
        lyo_datacenters.addWidget(lbl_dc_eida_ipgp_fr, 3,3)
        lyo_datacenters.addWidget(chb_dc_eida_sc3_infp_ro, 3,4)
        lyo_datacenters.addWidget(lbl_dc_eida_sc3_infp_ro, 3,5)
        lyo_datacenters.addWidget(chb_dc_eida_service_koeri_boun_edu_tr, 4,0)
        lyo_datacenters.addWidget(lbl_dc_eida_service_koeri_boun_edu_tr, 4,1)
        lyo_datacenters.addWidget(chb_dc_erde_geophysik_uni_muenchen_de, 4,2)
        lyo_datacenters.addWidget(lbl_dc_erde_geophysik_uni_muenchen_de, 4,3)
        lyo_datacenters.addWidget(chb_dc_fdsnws_raspberryshakedata_com, 4,4)
        lyo_datacenters.addWidget(lbl_dc_fdsnws_raspberryshakedata_com, 4,5)
        lyo_datacenters.addWidget(chb_dc_geofon_gfz_potsdam_de, 5,0)
        lyo_datacenters.addWidget(lbl_dc_geofon_gfz_potsdam_de, 5,1)
        lyo_datacenters.addWidget(chb_dc_rtserve_beg_utexas_edu, 5,2)
        lyo_datacenters.addWidget(lbl_dc_rtserve_beg_utexas_edu, 5,3)
        lyo_datacenters.addWidget(chb_dc_seisrequest_iag_usp_br, 5,4)
        lyo_datacenters.addWidget(lbl_dc_seisrequest_iag_usp_br, 5,5)
        lyo_datacenters.addWidget(chb_dc_webservices_ingv_it, 6,0)
        lyo_datacenters.addWidget(lbl_dc_webservices_ingv_it, 6,1)
        lyo_datacenters.addWidget(chb_dc_ws_icgc_cat, 6,2)
        lyo_datacenters.addWidget(lbl_dc_ws_icgc_cat, 6,3)
        lyo_datacenters.addWidget(chb_dc_ws_resif_fr, 6,4)
        lyo_datacenters.addWidget(lbl_dc_ws_resif_fr, 6,5)
        lyo_datacenters.addWidget(chb_dc_www_orfeus_eu_org, 7,0,1,1)
        lyo_datacenters.addWidget(lbl_dc_www_orfeus_eu_org, 7,1,1,5)
        lyo_datacenters.setContentsMargins(30,15,50,0)
        lyo_datacenters.setSpacing(10)
        # bottom 
        lyo_bottom = QGridLayout()
        lyo_bottom.addWidget(lbl_dlsetting,0,0,1,3)
        lyo_bottom.addWidget(lbl_dlscripts,0,3,1,2)
        lyo_bottom.addWidget(lbl_stalist, 1,0,1,1)
        lyo_bottom.addWidget(le_stalist, 1,1,1,1)
        lyo_bottom.addWidget(browse_stalist, 1,2,1,1)
        lyo_bottom.addWidget(chb_obspy,1,3,1,1)
        lyo_bottom.addWidget(lbl_obspy,1,4,1,1)
        lyo_bottom.addWidget(chb_fetch,2,3,1,1)
        lyo_bottom.addWidget(lbl_fetch,2,4,1,1)
        lyo_bottom.addWidget(lbl_stameta, 2,0,1,1)
        lyo_bottom.addWidget(le_stameta, 2,1,1,1)
        lyo_bottom.addWidget(browse_stameta, 2,2,1,1)
        lyo_bottom.addWidget(lbl_stalocs, 3,0,1,1)
        lyo_bottom.addWidget(le_stalocs, 3,1,1,2)
        lyo_bottom.addWidget(lbl_stachns, 4,0,1,1)
        lyo_bottom.addWidget(le_stachns, 4,1,1,2)
        lyo_bottom.addWidget(lbl_timelen, 5,0,1,1)
        lyo_bottom.addWidget(le_timelen, 5,1,1,2)
        lyo_bottom.setSpacing(10)
        lyo_bottom.setContentsMargins(30,30,50,30)

        self.layout = QVBoxLayout()
        self.layout.addLayout(lyo_datacenters)
        self.layout.addLayout(lyo_bottom)
        self.setLayout(self.layout)



class MSEED_to_SAC(QWidget):
    def __init__(self):
        super().__init__()

        # buttons graphics files
        icon_add = os.path.join(images_dir,"add.svg")
        icon_add_hover = os.path.join(images_dir,"add_hover.svg")
        if sys.platform == "win32":
            icon_add = icon_add.replace('\\','/')
            icon_add_hover = icon_add_hover.replace('\\','/')
        icon_remove = os.path.join(images_dir,"remove.svg")
        icon_remove_hover = os.path.join(images_dir,"remove_hover.svg")
        if sys.platform == "win32":
            icon_remove = icon_remove.replace('\\','/')
            icon_remove_hover = icon_remove_hover.replace('\\','/')

        
        self.le_input_mseeds = QLineEdit()
        self.le_input_mseeds.setPlaceholderText("Full path to input MSEED dataset dir")   
        self.browse_input_mseeds = MyDialog(type=3)
        self.le_output_sacs = QLineEdit()
        self.le_output_sacs.setPlaceholderText("Full path to input/output SAC dataset dir")
        self.browse_output_sacs = MyDialog(type=3)

        self.lyo_top = QGridLayout()
        self.lyo_top.addWidget(QLabel("Input MSEED dataset dir:"), 0,0)
        self.lyo_top.addWidget(self.le_input_mseeds, 0,1)
        self.lyo_top.addWidget(self.browse_input_mseeds, 0,2)
        self.lyo_top.addWidget(QLabel("Input/output SAC dataset dir:"), 1,0)
        self.lyo_top.addWidget(self.le_output_sacs, 1,1)
        self.lyo_top.addWidget(self.browse_output_sacs, 1,2)
        self.lyo_top.setContentsMargins(10,0,10,0)


        self.scroll = QScrollArea()
        self.scroll.setFrameShape(QFrame.Box)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.lyo_procs_mseed2sac = QVBoxLayout(self.scroll_widget)
        self.lyo_procs_mseed2sac.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_widget)
        self.add_rem_btns_mseed2sac = QWidget()
        self.add_rem_btns_mseed2sac.setObjectName("add_rem_btns_mseed2sac")
        self.add_rem_btns_mseed2sac.setStyleSheet("QPushButton {min-width: 35px; max-width: 35px;\
                                                 min-height: 35px; max-height: 35px;\
                                                 margin-top: 0px; margin-bottom: 0px; }\
                                    QPushButton:pressed {border: 3px solid #EEE;}")
        # Add process button
        self.btn_mseed2sac_add = QPushButton()
        self.btn_mseed2sac_add.setCursor(Qt.PointingHandCursor)
        self.btn_mseed2sac_add.setObjectName("btn_mseed2sac_add")
        qss_code = '''
            #btn_mseed2sac_add {
                image: url(%s);
            }

            #btn_mseed2sac_add:hover {
                image: url(%s);
            }
        ''' %(icon_add, icon_add_hover)
        self.btn_mseed2sac_add.setStyleSheet(qss_code)

        # Remove process button
        self.btn_mseed2sac_remove = QPushButton()
        self.btn_mseed2sac_remove.setCursor(Qt.PointingHandCursor)
        self.btn_mseed2sac_remove.setObjectName("btn_mseed2sac_remove")
        qss_code = '''
            #btn_mseed2sac_remove {
                image: url(%s);
            }

            #btn_mseed2sac_remove:hover {
                image: url(%s);
            }
        ''' %(icon_remove, icon_remove_hover)
        self.btn_mseed2sac_remove.setStyleSheet(qss_code)

        self.lyo_buttons = QHBoxLayout()
        self.lyo_buttons.addWidget(self.btn_mseed2sac_remove)
        self.lyo_buttons.addWidget(self.btn_mseed2sac_add)
        self.lyo_buttons.setAlignment(Qt.AlignCenter)
        self.add_rem_btns_mseed2sac.setLayout(self.lyo_buttons)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.lyo_top)
        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.add_rem_btns_mseed2sac)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10,20,10,10)
        self.setLayout(self.layout)

        # button signals and slots
        self.btn_mseed2sac_add.clicked.connect(lambda: self.add_proc())
        self.btn_mseed2sac_remove.clicked.connect(lambda: self.remove_proc())

    def proc_widget(self):
        # self.setAutoFillBackground(True)
        # palette = self.palette()
        # palette.setColor(QPalette.Window, QColor(color))
        # self.setPalette(palette)
        proc = QFrame()
        # proc_height = "180px";
        # proc.setFixedHeight(180)
        # proc.setObjectName("proc_widget")
        # proc.setStyleSheet("#proc_widget QFrame {background-color: #CDCDCD; min-height: %s; max-height: %s; border-radius: 10px; margin: 3px; margin-right: 5px}" %(proc_height, proc_height))

        proc_left = QFrame()
        # proc_left.setStyleSheet("max-width: 200px")
        proc_right = QFrame()

        cmb_proc = QComboBox()
        cmb_proc.setPlaceholderText("text")
        cmb_proc.addItem("---choose process---")
        cmb_proc.addItem("MSEED to SAC")
        cmb_proc.addItem("Remove extra channels")
        cmb_proc.addItem("Decimate")
        cmb_proc.addItem("Cut seismograms")
        cmb_proc.addItem("Remove response")
        cmb_proc.addItem("Bandpass filter")

        lyo_proc_left = QGridLayout()
        lyo_proc_left.addWidget(cmb_proc, 0,0,1,2)
        lyo_proc_left.addWidget(QLabel(), 1,0,1,2)
        lyo_proc_left.setAlignment(Qt.AlignLeft)

        lyo_proc_right = QVBoxLayout()

        proc_left.setLayout(lyo_proc_left)
        proc_right.setLayout(lyo_proc_right)

        lyo_proc = QHBoxLayout()
        lyo_proc.addWidget(proc_left)
        lyo_proc.addWidget(proc_right)
        lyo_proc.setContentsMargins(20,20,20,20)
        # lyo_proc.setContentsMargins(0,0,0,0)

        proc.setLayout(lyo_proc)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#FF0000"))
        proc.setAutoFillBackground(True)
        proc.setPalette(palette)

        return proc


    def add_proc(self):
        nprocs = self.lyo_procs_mseed2sac.count()
        widget_name = f"proc_{nprocs}"
        proc = self.proc_widget()
        proc.setObjectName(widget_name)
        self.lyo_procs_mseed2sac.addWidget(proc)

    def remove_proc(self):
        nprocs = int(self.lyo_procs_mseed2sac.count())
        if nprocs:
            widget_obj = self.lyo_procs_mseed2sac.itemAt(nprocs - 1).widget()
            widget_obj.deleteLater()



class SAC_to_NCF(MSEED_to_SAC):
    def __init__(self):
        super().__init__()


class NCF_to_EGF(MSEED_to_SAC):
    def __init__(self):
        super().__init__()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        app_icon = QIcon()
        app_icon.addFile(os.path.join(images_dir,'icons','16x16.png'))
        app_icon.addFile(os.path.join(images_dir,'icons','24x24.png'))
        app_icon.addFile(os.path.join(images_dir,'icons','32x32.png'))
        app_icon.addFile(os.path.join(images_dir,'icons','48x48.png'))
        app_icon.addFile(os.path.join(images_dir,'icons','256x256.png'))
        self.setWindowIcon(app_icon)
        self.setWindowTitle("ANS")

        # global vars
        global btn_menu
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
        global header_left
        global body_main

        # load external stylesheet file
        with open(os.path.join(pkg_dir,'gui.qss')) as qss:
            qss = qss.read()
            if sys.platform == 'darwin':
                qss = "\nQFrame { font-family: 'Tahoma';\n font-size: 14pt;}\n" + qss
            else:
                qss = "\nQFrame { font-family: 'Tahoma';\n font-size: 11pt;}\n" + qss
        self.setStyleSheet(qss)

        #### HEADER ####
        # header: left
        self.header_left = QFrame()
        self.header_left.setObjectName("header_left")
        lyo_header_left = QHBoxLayout()
        btn_menu = QPushButton()
        btn_menu.setObjectName("btn_menu")
        btn_menu.setCursor(Qt.PointingHandCursor)
        lyo_header_left.addWidget(btn_menu)
        lyo_header_left.setAlignment(Qt.AlignLeft)
        lyo_header_left.setSpacing(10)
        lyo_header_left.setContentsMargins(10,10,0,10)
        self.header_left.setLayout(lyo_header_left)

        #header: right
        self.header_right = QFrame()
        self.header_right.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,\
                                            QSizePolicy.Expanding))
        self.header_right.setObjectName("header_right")
        lyo_header_right = QHBoxLayout()
        btn_logo = QPushButton()
        btn_logo.setEnabled(False)
        btn_logo.setObjectName("btn_logo")
        lbl_title = QLabel("Ambient Noise Seismology (ANS)")
        lbl_title.setObjectName("lbl_title")
        lyo_header_right.addWidget(btn_logo)
        lyo_header_right.addWidget(lbl_title)
        lyo_header_right.setAlignment(Qt.AlignCenter)
        lyo_header_right.setSpacing(5)
        lyo_header_right.setContentsMargins(10,10,0,10)
        self.header_right.setLayout(lyo_header_right)


        # HEADER: LAYOUT
        header = QFrame()
        header.setObjectName("header")
        lyo_header = QHBoxLayout()
        lyo_header.addWidget(self.header_left)
        lyo_header.addWidget(self.header_right)
        lyo_header.setSpacing(0)
        lyo_header.setContentsMargins(0,0,0,0)
        header.setLayout(lyo_header)

        #### BODY ####
        # body: menu
        self.body_menu = QFrame()
        self.body_menu.setObjectName("body_menu")
        menu_top = QFrame()
        menu_top.setObjectName("menu_top")
        btn_setting = QPushButton()
        btn_setting.setObjectName("btn_setting")
        btn_setting.setCursor(Qt.PointingHandCursor)
        btn_download = QPushButton()
        btn_download.setObjectName("btn_download")
        btn_download.setCursor(Qt.PointingHandCursor)
        btn_mseed2sac = QPushButton()
        btn_mseed2sac.setObjectName("btn_mseed2sac")
        btn_mseed2sac.setCursor(Qt.PointingHandCursor)
        btn_sac2ncf = QPushButton()
        btn_sac2ncf.setObjectName("btn_sac2ncf")
        btn_sac2ncf.setCursor(Qt.PointingHandCursor)
        btn_ncf2egf = QPushButton()
        btn_ncf2egf.setObjectName("btn_ncf2egf")
        btn_ncf2egf.setCursor(Qt.PointingHandCursor)

        menu_bottom = QFrame()
        menu_bottom.setObjectName("menu_bottom")
        btn_terminal = QPushButton()
        btn_terminal.setObjectName("btn_terminal")
        btn_terminal.setCursor(Qt.PointingHandCursor)
        btn_about = QPushButton()
        btn_about.setObjectName("btn_about")
        btn_about.setCursor(Qt.PointingHandCursor)
        lyo_menu_top = QVBoxLayout()
        lyo_menu_top.addWidget(btn_setting)
        lyo_menu_top.addWidget(btn_download)
        lyo_menu_top.addWidget(btn_mseed2sac)
        lyo_menu_top.addWidget(btn_sac2ncf)
        lyo_menu_top.addWidget(btn_ncf2egf)
        lyo_menu_top.setAlignment(Qt.AlignTop)
        lyo_menu_top.setSpacing(10)
        lyo_menu_top.setContentsMargins(10,10,10,0)
        lyo_menu_bottom = QVBoxLayout()
        lyo_menu_bottom.addWidget(btn_terminal)
        lyo_menu_bottom.addWidget(btn_about)
        lyo_menu_bottom.setAlignment(Qt.AlignBottom)
        lyo_menu_bottom.setSpacing(10)
        lyo_menu_bottom.setContentsMargins(10,10,0,10)
        lyo_menu_top.addStretch(1)
        menu_top.setLayout(lyo_menu_top)
        menu_bottom.setLayout(lyo_menu_bottom)
        lyo_body_menu = QVBoxLayout()
        lyo_body_menu.addWidget(menu_top)
        lyo_body_menu.addWidget(menu_bottom)
        lyo_body_menu.setSpacing(0)
        lyo_body_menu.setContentsMargins(0,0,0,0)
        self.body_menu.setLayout(lyo_body_menu)

        # body: main
        self.body_main = QStackedWidget()
        self.body_main.setObjectName("body_main")
        self.body_main.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,\
                                            QSizePolicy.MinimumExpanding))
        setting = Project_Setting()
        download = Download()
        mseed2sac = MSEED_to_SAC()
        sac2ncf = SAC_to_NCF()
        ncf2egf = NCF_to_EGF()

        self.body_main.addWidget(setting)
        self.body_main.addWidget(download)
        self.body_main.addWidget(mseed2sac)
        self.body_main.addWidget(sac2ncf)
        self.body_main.addWidget(ncf2egf)

        # BODY: LAYOUT
        body = QFrame()
        body.setObjectName("body")
        lyo_body = QHBoxLayout()
        lyo_body.addWidget(self.body_menu)
        lyo_body.addWidget(self.body_main)
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
        lbl_status = QLabel('Ready...')
        lbl_status.setObjectName("lbl_status")
        lyo_footer_left.addWidget(lbl_status)
        lyo_footer_left.setAlignment(Qt.AlignLeft)
        footer_left.setLayout(lyo_footer_left)

        # footer_right
        lyo_footer_right = QHBoxLayout()
        btn_save = QPushButton()
        btn_save.setObjectName("btn_save")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_discard = QPushButton()
        btn_discard.setObjectName("btn_discard")
        btn_discard.setCursor(Qt.PointingHandCursor)
        btn_revert = QPushButton()
        btn_revert.setObjectName("btn_revert")
        btn_revert.setCursor(Qt.PointingHandCursor)
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

        # PATH to BUTTON ICONS
        # logo
        icon_logo = os.path.join(images_dir,"ans_logo.svg")
        if sys.platform == "win32":
            icon_logo = icon_logo.replace('\\','/')
        # menu
        icon_menu = os.path.join(images_dir,"menu.svg")
        icon_menu_hover = os.path.join(images_dir,"menu_hover.svg")
        if sys.platform == "win32":
            icon_menu = icon_menu.replace('\\','/')
            icon_menu_hover = icon_menu_hover.replace('\\','/')
        # setting
        self.icon_setting = os.path.join(images_dir,"setting.svg")
        self.icon_setting_hover = os.path.join(images_dir,"setting_hover.svg")
        self.icon_setting_selected = os.path.join(images_dir,"setting_selected.svg")
        if sys.platform == "win32":
            self.icon_setting = self.icon_setting.replace('\\','/')
            self.icon_setting_hover = self.icon_setting_hover.replace('\\','/')
            self.icon_setting_selected = self.icon_setting_selected.replace('\\','/')
        # download            
        self.icon_download = os.path.join(images_dir,"download.svg")
        self.icon_download_hover = os.path.join(images_dir,"download_hover.svg")
        self.icon_download_selected = os.path.join(images_dir,"download_selected.svg")
        if sys.platform == "win32":
            self.icon_download = self.icon_download.replace('\\','/')
            self.icon_download_hover = self.icon_download_hover.replace('\\','/')
            self.icon_download_selected = self.icon_download_selected.replace('\\','/')
        # mseed2sac
        self.icon_mseed2sac = os.path.join(images_dir,"mseed2sac.svg")
        self.icon_mseed2sac_hover = os.path.join(images_dir,"mseed2sac_hover.svg")
        self.icon_mseed2sac_selected = os.path.join(images_dir,"mseed2sac_selected.svg")
        if sys.platform == "win32":
            self.icon_mseed2sac = self.icon_mseed2sac.replace('\\','/')
            self.icon_mseed2sac_hover = self.icon_mseed2sac_hover.replace('\\','/')
            self.icon_mseed2sac_selected = self.icon_mseed2sac_selected.replace('\\','/')
        # sac2ncf
        self.icon_sac2ncf = os.path.join(images_dir,"sac2ncf.svg")
        self.icon_sac2ncf_hover = os.path.join(images_dir,"sac2ncf_hover.svg")
        self.icon_sac2ncf_selected = os.path.join(images_dir,"sac2ncf_selected.svg")
        if sys.platform == "win32":
            self.icon_sac2ncf = self.icon_sac2ncf.replace('\\','/')
            self.icon_sac2ncf_hover = self.icon_sac2ncf_hover.replace('\\','/')
            self.icon_sac2ncf_selected = self.icon_sac2ncf_selected.replace('\\','/')
        # ncf2egf
        self.icon_ncf2egf = os.path.join(images_dir,"ncf2egf.svg")
        self.icon_ncf2egf_hover = os.path.join(images_dir,"ncf2egf_hover.svg")
        self.icon_ncf2egf_selected = os.path.join(images_dir,"ncf2egf_selected.svg")
        if sys.platform == "win32":
            self.icon_ncf2egf = self.icon_ncf2egf.replace('\\','/')
            self.icon_ncf2egf_hover = self.icon_ncf2egf_hover.replace('\\','/')
            self.icon_ncf2egf_selected = self.icon_ncf2egf_selected.replace('\\','/')
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
        
        # APPLY BUTTON QSS
        self.set_btn_qss(btn_logo, "btn_logo", (50, 50), icon_logo, icon_logo, 3,'#DDDDF9')
        self.set_btn_qss(btn_menu, "btn_menu", (176,40), icon_menu, icon_menu_hover, 1,'#DDDDF9')
        self.set_btn_qss(btn_setting, "btn_setting", (176,40), self.icon_setting, self.icon_setting_hover, 1,'#DDDDF9')
        self.set_btn_qss(btn_download, "btn_download", (176,40), self.icon_download, self.icon_download_hover, 1,'#DDDDF9')
        self.set_btn_qss(btn_mseed2sac, "btn_mseed2sac", (176,40), self.icon_mseed2sac, self.icon_mseed2sac_hover, 1,'#DDDDF9')
        self.set_btn_qss(btn_sac2ncf, "btn_sac2ncf", (176,40), self.icon_sac2ncf, self.icon_sac2ncf_hover, 1,'#DDDDF9')
        self.set_btn_qss(btn_ncf2egf, "btn_ncf2egf", (176,40), self.icon_ncf2egf, self.icon_ncf2egf_hover, 1,'#DDDDF9')
        self.set_btn_qss(btn_terminal, "btn_terminal", (176,40), icon_terminal, icon_terminal_hover, 1,'#DDDDF9')
        self.set_btn_qss(btn_about, "btn_about", (176,40), icon_about, icon_about_hover, 1,'#DDDDF9')
        self.set_btn_qss(btn_revert, "btn_revert", (167,35), icon_revert, icon_revert_hover,2,'#DDDDF9')
        self.set_btn_qss(btn_discard, "btn_discard", (167,35), icon_discard, icon_discard_hover,2,'#DDDDF9')
        self.set_btn_qss(btn_save, "btn_save", (167,35), icon_save, icon_save_hover,2,'#DDDDF9')

        # SIGNALS ans SLOTS
        btn_setting.clicked.connect(lambda: self.body_main.setCurrentIndex(0))
        btn_download.clicked.connect(lambda: self.body_main.setCurrentIndex(1))
        btn_mseed2sac.clicked.connect(lambda: self.body_main.setCurrentIndex(2))
        btn_sac2ncf.clicked.connect(lambda: self.body_main.setCurrentIndex(3))
        btn_ncf2egf.clicked.connect(lambda: self.body_main.setCurrentIndex(4))
        btn_setting.clicked.connect(lambda: self.selected_widget_tab(0))
        btn_download.clicked.connect(lambda: self.selected_widget_tab(1))
        btn_mseed2sac.clicked.connect(lambda: self.selected_widget_tab(2))
        btn_sac2ncf.clicked.connect(lambda: self.selected_widget_tab(3))
        btn_ncf2egf.clicked.connect(lambda: self.selected_widget_tab(4))
        btn_menu.clicked.connect(self.toggle_menu)


        #### EXTRA STEPS BEFORE RUNNIG THE APP ####

        # fix failing to update self on Mac!
        QCoreApplication.processEvents()
        self.header_left.setStyleSheet("max-width: 190px")
        self.body_menu.setStyleSheet("max-width: 190px")
        self.toggle_menu()

        # select widget 0
        self.selected_widget_tab(2)
        self.body_main.setCurrentIndex(2)

        # hide terminal button (for the first versions)
        btn_terminal.setVisible(False)


    def selected_widget_tab(self, widget_index): # apply proper qss to the selected widget button
        if widget_index == 0:
            self.set_btn_qss(btn_setting, "btn_setting", (176,40), self.icon_setting_selected, self.icon_setting_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_download, "btn_download", (176,40), self.icon_download, self.icon_download_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_mseed2sac, "btn_mseed2sac", (176,40), self.icon_mseed2sac, self.icon_mseed2sac_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_sac2ncf, "btn_sac2ncf", (176,40), self.icon_sac2ncf, self.icon_sac2ncf_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_ncf2egf, "btn_ncf2egf", (176,40), self.icon_ncf2egf, self.icon_ncf2egf_hover, 1,'#DDDDF9')
        elif widget_index == 1:
            self.set_btn_qss(btn_setting, "btn_setting", (176,40), self.icon_setting, self.icon_setting_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_download, "btn_download", (176,40), self.icon_download_selected, self.icon_download_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_mseed2sac, "btn_mseed2sac", (176,40), self.icon_mseed2sac, self.icon_mseed2sac_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_sac2ncf, "btn_sac2ncf", (176,40), self.icon_sac2ncf, self.icon_sac2ncf_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_ncf2egf, "btn_ncf2egf", (176,40), self.icon_ncf2egf, self.icon_ncf2egf_hover, 1,'#DDDDF9')
        elif widget_index == 2:
            self.set_btn_qss(btn_setting, "btn_setting", (176,40), self.icon_setting, self.icon_setting_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_download, "btn_download", (176,40), self.icon_download, self.icon_download_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_mseed2sac, "btn_mseed2sac", (176,40), self.icon_mseed2sac_selected, self.icon_mseed2sac_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_sac2ncf, "btn_sac2ncf", (176,40), self.icon_sac2ncf, self.icon_sac2ncf_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_ncf2egf, "btn_ncf2egf", (176,40), self.icon_ncf2egf, self.icon_ncf2egf_hover, 1,'#DDDDF9')
        elif widget_index == 3:
            self.set_btn_qss(btn_setting, "btn_setting", (176,40), self.icon_setting, self.icon_setting_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_download, "btn_download", (176,40), self.icon_download, self.icon_download_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_mseed2sac, "btn_mseed2sac", (176,40), self.icon_mseed2sac, self.icon_mseed2sac_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_sac2ncf, "btn_sac2ncf", (176,40), self.icon_sac2ncf_selected, self.icon_sac2ncf_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_ncf2egf, "btn_ncf2egf", (176,40), self.icon_ncf2egf, self.icon_ncf2egf_hover, 1,'#DDDDF9')
        elif widget_index == 4:
            self.set_btn_qss(btn_setting, "btn_setting", (176,40), self.icon_setting, self.icon_setting_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_download, "btn_download", (176,40), self.icon_download, self.icon_download_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_mseed2sac, "btn_mseed2sac", (176,40), self.icon_mseed2sac, self.icon_mseed2sac_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_sac2ncf, "btn_sac2ncf", (176,40), self.icon_sac2ncf, self.icon_sac2ncf_hover, 1,'#DDDDF9')
            self.set_btn_qss(btn_ncf2egf, "btn_ncf2egf", (176,40), self.icon_ncf2egf_selected, self.icon_ncf2egf_hover, 1,'#DDDDF9')
        else:
            pass

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
                border-top: %dpx solid %s;
                border-right: %dpx solid %s;
            }
        ''' %(btn_obj_name, btn_size[0], btn_size[0], btn_size[1], btn_size[1],\
              icon_file, btn_obj_name, icon_hover_file, btn_obj_name,\
              icon_clicked_border_size, icon_clicked_border_color,\
              icon_clicked_border_size, icon_clicked_border_color)
        btn_obj.setStyleSheet(qss_code)

    
    def toggle_menu(self):
        self.anim_body_main = QPropertyAnimation(self.body_main, b'minimumWidth')
        self.anim_body_menu = QPropertyAnimation(self.body_menu, b'maximumWidth')
        self.anim_header_right = QPropertyAnimation(self.header_right, b'minimumWidth')
        self.anim_header_left = QPropertyAnimation(self.header_left, b'maximumWidth')
        self.anim_body_main.setDuration(170)
        self.anim_body_menu.setDuration(170)
        self.anim_header_left.setDuration(170)
        self.anim_header_right.setDuration(170)
        maxWidth = self.width() - 60
        minWidth = self.width() - 190
        if self.body_menu.width() != 60:
            self.anim_body_main.setEndValue(self.width() - 60)
            self.anim_body_menu.setEndValue(60)
            self.anim_header_right.setEndValue(self.width() - 60)
            self.anim_header_left.setEndValue(60)
        else:
            self.anim_body_main.setEndValue(self.width() - 190)
            self.anim_body_menu.setEndValue(190)
            self.anim_header_right.setEndValue(self.width() - 190)
            self.anim_header_left.setEndValue(190)
        self.anim_body_menu.start()
        self.anim_body_main.start()
        self.anim_header_left.start()
        self.anim_header_right.start()

    

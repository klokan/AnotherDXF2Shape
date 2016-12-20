# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiADXF2Shape
    Änderungen V0.4:
        23.11.16:
            - Stapelimport integriert
            - Textformatierungen optional umsetzen
            
    Änderungen V0.3:
        06.07.16:
            - OGR-Version anzeigen
                                 A QGIS plugin
 KonverDXF to shape and add to QGIS
                             -------------------
        begin                : 2016-06-20
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Mike Blechschmidt EZUSoft 
        email                : qgis@makobo.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.utils import os, sys
from PyQt4.QtCore import QSettings,QSize
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QMessageBox, QDialogButtonBox
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from fnc4all import *
from clsDXFTools import DXFImporter
import clsADXF2Shape

# Programm funktioniert auch ohne installierte gdal-Bibliothek, die Bibo wird nur zur Anzeige der Version genommen
try:
   import gdal
except:
   pass
 
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiADXF2Shape.ui'))
from PyQt4.QtCore import QObject, QEvent

"""
    23.11.16: D&D deaktiviert
class QLineEditDropHandler(QObject):

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.DragEnter:
            # we need to accept this event explicitly to be able to receive QDropEvents!
            event.accept()
        if event.type() == QEvent.Drop:
            md = event.mimeData()
            if md.hasUrls():
                for url in md.urls():
                    # D&D von Serverdateien (ohne LW) funktioniert nicht - Problem ignoriert
                    # Pfad für Windows korrigieren, da dieser immer mit "/" beginnt
                    # /D:/Testdaten/ALKIS_Testdaten_Hessen.dxf
                    if url.path()[0:1] == "/" and url.path()[2:3]==":":
                       obj.setText(url.path()[1:]) 
                    else:
                        obj.setText(url.path())
                    break
            event.accept()
        return QObject.eventFilter(self, obj, event)
"""        

class uiADXF2Shape(QtGui.QDialog, FORM_CLASS):
    charsetList = ["System",
     "ascii",
     "big5",
     "big5hkscs",
     "cp037",
     "cp424",
     "cp437",
     "cp500",
     "cp720",
     "cp737",
     "cp775",
     "cp850",
     "cp852",
     "cp855",
     "cp856",
     "cp857",
     "cp858",
     "cp860",
     "cp861",
     "cp862",
     "cp863",
     "cp864",
     "cp865",
     "cp866",
     "cp869",
     "cp874",
     "cp875",
     "cp932",
     "cp949",
     "cp950",
     "cp1006",
     "cp1026",
     "cp1140",
     "cp1250",
     "cp1251",
     "cp1252",
     "cp1253",
     "cp1254",
     "cp1255",
     "cp1256",
     "cp1257",
     "cp1258",
     "euc_jp",
     "euc_jis_2004",
     "euc_jisx0213",
     "euc_kr",
     "gb2312",
     "gbk",
     "gb18030",
     "hz",
     "iso2022_jp",
     "iso2022_jp_1",
     "iso2022_jp_2",
     "iso2022_jp_2004",
     "iso2022_jp_3",
     "iso2022_jp_ext",
     "iso2022_kr",
     "latin_1",
     "iso8859_2",
     "iso8859_3",
     "iso8859_4",
     "iso8859_5",
     "iso8859_6",
     "iso8859_7",
     "iso8859_8",
     "iso8859_9",
     "iso8859_10",
     "iso8859_13",
     "iso8859_14",
     "iso8859_15",
     "iso8859_16",
     "johab",
     "koi8_r",
     "koi8_u",
     "mac_cyrillic",
     "mac_greek",
     "mac_iceland",
     "mac_latin2",
     "mac_roman",
     "mac_turkish",
     "ptcp154",
     "shift_jis",
     "shift_jis_2004",
     "shift_jisx0213",
     "System",
     "utf_32",
     "utf_32_be",
     "utf_32_le",
     "utf_16",
     "utf_16_be",
     "utf_16_le",
     "utf_7",
     "utf_8",
     "utf_8_sig"]
    def __init__(self, parent=None):
        """Constructor."""
        super(uiADXF2Shape, self).__init__(parent)
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'translation_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            translator = QTranslator()
            translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(translator)

        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.browseDXFDatei.clicked.connect(self.browseDXFDatei_clicked)    
        self.browseZielPfad.clicked.connect(self.browseZielPfad_clicked) 
        self.chkSHP.clicked.connect(self.chkSHP_clicked)    
        self.btnStart.clicked.connect(self.btnStart_clicked)          
        
        # Per Code alle Elemente beschriften die ein  "\n" enthalten, denn  das kann der Form-Tranlator nicht
        #self.chkCol.setText (self.tr(u"Geometriecollektion \n(Blöcke/Signaturen)\nseparat ausspielen"))
        #self.chkLay.setText (self.tr(u"Layer einzeln gruppieren\n(zeitaufwändig)"))
        #self.chkCol.setText (self.tr("use geometry collection"))
        #self.chkLay.setText (self.tr("group layer" + "\n" + "(takes a long time)"))        
        
        #self.chkSHP.setText (self.tr(u"als Shape-Dateien speichern"))
        #self.txtDXFDatNam.setPlaceholderText(self.tr(u"DXF-Datei eingeben")) 
        #self.lbDXF.setText(self.tr(u"DXF-Quelldatei"))
        

        # Letzte Werte lesen
        s = QSettings( "EZUSoft", "ADXF2Shape" )
        
        bGenCol = True if s.value( "bGenCol", "Nein" ) == "Ja" else False
        self.chkCol.setChecked(bGenCol)

        bGenLay = True if s.value( "bGenLay", "Ja" ) == "Ja" else False
        self.chkLay.setChecked(bGenLay)
        
        bFormatText = True if s.value( "bFormatText", "Ja" ) == "Ja" else False
        self.chkUseTextFormat.setChecked(bFormatText)
        
        bUseColor4Point = True if s.value( "bUseColor4Point", "Ja" ) == "Ja" else False
        self.chkUseColor4Point.setChecked(bUseColor4Point)
        bUseColor4Line = True if s.value( "bUseColor4Line", "Ja" ) == "Ja" else False
        self.chkUseColor4Line.setChecked(bUseColor4Line)
        bUseColor4Poly = True if s.value( "bUseColor4Poly", "Nein" ) == "Ja" else False
        self.chkUseColor4Poly.setChecked(bUseColor4Poly)
        
        bGenSHP = True if s.value( "bGenSHP", "Nein" ) == "Ja" else False
        self.chkSHP.setChecked(bGenSHP)
        self.chkSHP_clicked()
        
        iCodePage=s.value( "iCodePage", 0 ) 
        self.txtFaktor.setText('1.3')


        self.cbCharSet.addItems(self.charsetList)
        self.cbCharSet.setCurrentIndex(int(iCodePage))
        try:
            self.lbGDAL.setText(gdal.VersionInfo("GDAL_RELEASE_DATE"))
        except:
            self.lbGDAL.setText("-")
        self.StartHeight=self.height()
        self.StartMinHeight=self.minimumHeight()
        # Drag & Drop Event
        #if not fncDebugMode():
            # Kommt bei Programmfehleren immer wieder zu komischen Effekten/Abstüzen - deshalb wärend der Entwicklung deaktivieren
            # 23.11.16: D&D deaktiviert, da nicht sichergestellt werden kann, dass alle Dateien aus einem Verzeichnis kommen
            #               und der Anpassungsaufwand im Moment nicht lohnt
            #self.listDXFDatNam.installEventFilter(QLineEditDropHandler(self))
            #self.txtZielPfad.installEventFilter(QLineEditDropHandler(self))
            
        listEmpty = self.tr("no DXF-file selected")
        self.listDXFDatNam.addItem (listEmpty)
        self.listDXFDatNam.setEnabled(False)  
        self.listEmpty=listEmpty
        self.FormRunning(False)
    # noinspection PyMethodMayBeStatic
    
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('uiADXF2Shape', message)
        
    def chkSHP_clicked(self):
        bGenSHP=self.chkSHP.isChecked()
        self.lbSHP.setEnabled(bGenSHP)      
        self.txtZielPfad.setEnabled(bGenSHP)      
        self.browseZielPfad.setEnabled(bGenSHP) 
        if bGenSHP:
            self.txtZielPfad.setPlaceholderText(self.tr("Specify destination path")) 
            self.lbSHP.setText(self.tr(u"Output shape path"))
        else:
            self.txtZielPfad.setPlaceholderText("") 
            self.lbSHP.setText("") 
    
         
    def browseDXFDatei_clicked(self):
        s = QSettings( "EZUSoft", "ADXF2Shape" )
        lastDXFDir = s.value("lastDXFDir", ".")
        """
        DXFDatName = QtGui.QFileDialog.getOpenFileName(self, 'Open File', lastDXFDir, 'DXF  (*.dxf)')
        self.txtDXFDatNam.setText(DXFDatName)
        (dxfDir, dxfFile) = os.path.split(DXFDatName)
        if dxfDir <> "":
            s.setValue("lastDXFDir", dxfDir)
        """
        MerkAnz=self.listDXFDatNam.count()
        Anz=0
        for DXFDatName in QtGui.QFileDialog.getOpenFileNames(self, 'Open File', lastDXFDir, 'DXF  (*.dxf)'):
            DXFDatName=(DXFDatName).replace("\\","/")
            if Anz == 0:
                # im Gegensatz zu getOpenFileName() gibt getOpenFileNames Backslash's zurück
                self.listDXFDatNam.clear()
                self.listDXFDatNam.setEnabled(True)     
                (dxfDir, dxfFile) = os.path.split(DXFDatName)
                if dxfDir <> "":
                    s.setValue("lastDXFDir", dxfDir) 
                #für Übergang    
                #printlog (DXFDatName)
                #self.txtDXFDatNam.setText(DXFDatName)
            Anz=Anz+1        
            self.listDXFDatNam.addItem(DXFDatName) 
            MerkAnz=Anz
        
        if MerkAnz > 1:
            #self.listDXFDatNam.setMaximumHeight(1000)
            self.listDXFDatNam.setMinimumHeight(40)
            self.setMinimumHeight = self.StartMinHeight+150
            if self.height() < self.StartHeight+150:
                self.resize(self.width(),self.StartHeight+150)
        else:
            self.listDXFDatNam.setMinimumHeight(20)
            self.setMinimumHeight = self.StartMinHeight
            #self.resize(self.width(),self.StartHeight)
        

    def browseZielPfad_clicked(self):
        s = QSettings( "EZUSoft", "ASHP2Shape" )
        lastSHPDir = s.value("lastSHPDir", ".")
        
        if not os.path.exists(lastSHPDir):
            lastSHPDir=os.getcwd()    
        flags = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
        shpDirName = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",lastSHPDir,flags)
        shpDirName=shpDirName.replace("\\","/")
        self.txtZielPfad.setText(shpDirName)
        #SHPDir, Dummy = os.path.split(shpDirName)
        #print "'" + SHPDir + "'" + "*"+"'" + Dummy + "'"
        if shpDirName <> "":
            s.setValue("lastSHPDir", shpDirName)
    
    def OptSpeichern(self):        
        s = QSettings( "EZUSoft", "ADXF2Shape" )
        s.setValue( "bGenCol", "Ja" if self.chkCol.isChecked() == True else "Nein")
        s.setValue( "bGenLay", "Ja" if self.chkLay.isChecked() == True else "Nein")
        s.setValue( "bGenSHP", "Ja" if self.chkSHP.isChecked() == True else "Nein")
        s.setValue( "bFormatText", "Ja" if self.chkUseTextFormat.isChecked() == True else "Nein")
        s.setValue( "bUseColor4Point", "Ja" if self.chkUseColor4Point.isChecked() == True else "Nein")
        s.setValue( "bUseColor4Line", "Ja" if self.chkUseColor4Line.isChecked() == True else "Nein")
        s.setValue( "bUseColor4Poly", "Ja" if self.chkUseColor4Poly.isChecked() == True else "Nein")
        
        s.setValue( "iCodePage", self.cbCharSet.currentIndex())
        
    
    def btnStart_clicked(self):
        # 0. Test ob eine DXF gewählt
        if self.listDXFDatNam.count() == 0 or (self.listDXFDatNam.count() == 1 and self.listDXFDatNam.item(0).text() == self.listEmpty):
            QMessageBox.critical(None,  self.tr("Please specify a DXF-File"),self.tr(u"DXF-file not selected")) 
            return

        # 1. Test ob alle dxf lesbar
        #allDXFDat = self.listDXFDatNam('', Qt.MatchRegExp)
        for i in xrange(self.listDXFDatNam.count()):
            AktDat=self.listDXFDatNam.item(i).text()
            if not os.path.exists(AktDat):
                QMessageBox.critical(None,self.tr(u"DXF-file not found"), AktDat )
                return


        # 2. Test ob ZielPfad vorhanden
        if self.chkSHP.isChecked():
            ZielPfad=self.txtZielPfad.text()
        else:
            ZielPfad=EZUTempDir()
            
        if ZielPfad == "":
            QMessageBox.critical(None, self.tr("Destination path not selected"), self.tr("Please specify a target path for shapes")) 
            return
        if ZielPfad[:-1] <> "/" and ZielPfad[:-1] <> "\\":
                ZielPfad=ZielPfad + "/"
        if not os.path.exists(ZielPfad):
            QMessageBox.critical(None, self.tr("Destination path not found"), ZielPfad)
            return
             
        #3. Test ob Faktor logisch            
        try:
            dblFaktor=float(self.txtFaktor.text().replace(",","."))
            if dblFaktor == 0:
                QMessageBox.critical(None, self.tr("Reset text height"), self.tr("Text correction factor can not assume a zero value") )
                self.txtFaktor.setText("1.3")
                return
        except:
            QMessageBox.critical(None , self.tr("Reset text height"), self.tr("Error converting Text correction factor to numbers"))
            self.txtFaktor.setText("1.3")
            return
            
        self.OptSpeichern()
        #           (DXFDatNam,shpPfad,  bSHPSave,                fontSize, fontSizeInMapUnits, bCol,bLayer)
        #self.FormRunning(True)

        #printlog (AktDat)
        #printlog (self.txtDXFDatNam.text())
        #return
    
        Antw = DXFImporter (self, self.listDXFDatNam, ZielPfad, self.chkSHP.isChecked(), self.cbCharSet.currentText(),self.chkCol.isChecked(),self.chkLay.isChecked(), self.chkUseTextFormat.isChecked(), self.chkUseColor4Point.isChecked(), self.chkUseColor4Line.isChecked(), self.chkUseColor4Poly.isChecked(), dblFaktor)
        self.FormRunning(False) # nur sicherheitshalber, falls in DXFImporter übersprungen/vergessen
        
    
        
    def SetAktionText(self,txt):
        self.lbAktion.setText(txt)
        self.repaint()   
    def SetAktionAktSchritt(self,akt):
        self.pgBar.setValue(akt)
        self.repaint()
        #QMessageBox.information(None, ("aktuell gesetzt"), str(akt))
    def SetAktionGesSchritte(self,ges):
        self.pgBar.setMaximum(ges)
        self.repaint()
        #QMessageBox.information(None, ("maximum gesetzt"), str(ges))
    
    def SetDatAktionText(self,txt):
        self.lbDatAktion.setText(txt)
        self.repaint()   
    def SetDatAktionAktSchritt(self,akt):
        self.pgDatBar.setValue(akt)
        self.repaint()
        #QMessageBox.information(None, ("aktuell gesetzt"), str(akt))
    def SetDatAktionGesSchritte(self,ges):
        self.pgDatBar.setMaximum(ges)
        self.repaint()
        #QMessageBox.information(None, ("maximum gesetzt"), str(ges))

    def FormRunning(self,bRun):
        def Anz(ctl):
            if bRun:
                ctl.hide()
            else:
                ctl.show()
        Anz(self.lbFormat); Anz(self.lbColor); Anz(self.lbGDAL); Anz(self.lbDXF); Anz(self.lbSHP); Anz(self.lblCharSet)
        Anz(self.chkUseTextFormat);Anz(self.chkUseColor4Point); Anz(self.chkUseColor4Line); Anz(self.chkUseColor4Poly)
 
        Anz(self.btnStart) 
        Anz(self.cbCharSet)
        Anz(self.button_box.button(QDialogButtonBox.Close))
        Anz(self.browseDXFDatei);Anz(self.browseZielPfad)
        Anz(self.listDXFDatNam);Anz(self.txtZielPfad)
        Anz(self.chkCol); Anz(self.chkLay); Anz(self.chkSHP)
        Anz(self.lbFaktor);Anz(self.txtFaktor)
        


        if bRun:
            self.lbIcon.show()
            self.pgBar.show()
            self.lbAktion.show()
            self.pgBar.setValue(0) 
            self.AktSchritt = 0 
            self.pgDatBar.show()
            self.lbDatAktion.show()
            self.pgDatBar.setValue(0) 
            self.AktDatSchritt = 0 
            # eventuell Shape aktivieren
            self.chkSHP_clicked()
        else:
            self.lbIcon.hide()
            self.pgBar.hide()
            self.lbAktion.hide()
            self.pgDatBar.hide()
            self.lbDatAktion.hide()

    def RunMenu(self):
        self.exec_()
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

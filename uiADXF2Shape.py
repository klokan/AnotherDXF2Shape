# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiADXF2Shape
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
from PyQt4.QtCore import QSettings
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QMessageBox, QDialogButtonBox
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from fnc4all import *
from clsDXFTools import StartImport
import clsADXF2Shape

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiADXF2Shape.ui'))
from PyQt4.QtCore import QObject, QEvent

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
        

class uiADXF2Shape(QtGui.QDialog, FORM_CLASS):
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
        
        bGenCol = True if s.value( "bGenCol", "Ja" ) == "Ja" else False
        self.chkCol.setChecked(bGenCol)

        bGenLay = True if s.value( "bGenLay", "Nein" ) == "Ja" else False
        self.chkLay.setChecked(bGenLay)
        
        bGenSHP = True if s.value( "bGenSHP", "Nein" ) == "Ja" else False
        self.chkSHP.setChecked(bGenSHP)
        self.chkSHP_clicked()

        self.txtHoe.setText(s.value( "dblHoe", '2' ))
        
        self.cbUnit.addItem(self.tr("Map unit"))
        self.cbUnit.addItem(self.tr("Millimeter"))
        iUnit=s.value( "iUnit", 0 )
        self.cbUnit.setCurrentIndex(int(iUnit)) # unter Linux war/ist Int() notwendig


        # Drag & Drop Event
        if not fncDebugMode():
            # Kommt bei Programmfehleren immer wieder zu komischen Effekten/Abstüzen - deshalb wärend der Entwicklung deaktivieren
            self.txtDXFDatNam.installEventFilter(QLineEditDropHandler(self))
            self.txtZielPfad.installEventFilter(QLineEditDropHandler(self))

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
        DXFDatName = QtGui.QFileDialog.getOpenFileName(self, 'Open File', lastDXFDir, 'DXF  (*.dxf)')
        self.txtDXFDatNam.setText(DXFDatName)
        (dxfDir, dxfFile) = os.path.split(DXFDatName)
        if dxfDir <> "":
            s.setValue("lastDXFDir", dxfDir)
    
    def browseZielPfad_clicked(self):
        s = QSettings( "EZUSoft", "ASHP2Shape" )
        lastSHPDir = s.value("lastSHPDir", ".")
        
        if not os.path.exists(lastSHPDir):
            lastSHPDir=os.getcwd()    
        flags = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
        shpDirName = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",lastSHPDir,flags)

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
        s.setValue( "dblHoe", str(self.txtHoe.text()))
        s.setValue( "iUnit", self.cbUnit.currentIndex())
    
    def btnStart_clicked(self):
        Antw=self.StartImport()

 
    def StartImport (self):
        # 1. Test ob dxf lesbar
        AktDat=self.txtDXFDatNam.text()
        if AktDat == "":
            QMessageBox.critical(None,  self.tr(u"DXF-file not selected"), self.tr("Please specify a DXF-File")) 
            return
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
             
        # 3. Text ob Texthöhe i.o               
        try:
            dblHoe=float(self.txtHoe.text().replace(",","."))
            if dblHoe == 0:
                QMessageBox.critical(None, self.tr("Reset text height"), self.tr("Text height can not assume a zero value") )
                self.txtHoe.setText("2")
                return
        except:
            QMessageBox.critical(None , self.tr("Reset text height"), self.tr("Error converting text to numbers"))
            self.txtHoe.setText("2")
            return
            
        self.OptSpeichern()
        #           (DXFDatNam,shpPfad,  bSHPSave,                fontSize, fontSizeInMapUnits, bCol,bLayer)
        #self.FormRunning(True)
        Antw = StartImport (self,AktDat,   ZielPfad, self.chkSHP.isChecked(), dblHoe, self.cbUnit.currentIndex() == 0, self.chkCol.isChecked(),self.chkLay.isChecked())
        self.FormRunning(False)
   
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
    
    def FormRunning(self,bRun):
        def Anz(ctl):
            if bRun:
                ctl.hide()
            else:
                ctl.show()
        Anz(self.btnStart) 
        Anz(self.txtHoe)
        Anz(self.cbUnit)
        Anz(self.button_box.button(QDialogButtonBox.Close))
        Anz(self.browseDXFDatei)
        Anz(self.browseZielPfad)
        Anz(self.txtDXFDatNam)
        Anz(self.txtZielPfad)
        Anz(self.chkCol)
        Anz(self.chkLay)
        Anz(self.chkSHP)
        Anz(self.lbDXF)
        Anz(self.lbSHP)
        Anz(self.lbFont)


        if bRun:
            self.lbIcon.show()
            self.pgBar.show()
            self.lbAktion.show()
            self.pgBar.setValue(0) 
            self.AktSchritt = 0 
            # eventuell Shape aktivieren
            self.chkSHP_clicked()
        else:
            self.lbIcon.hide()
            self.pgBar.hide()
            self.lbAktion.hide()

    def RunMenu(self):
        self.exec_()
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

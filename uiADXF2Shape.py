# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiADXF2Shape
    Stand 10.11.2017: Einheitliche Grundlage QT4/QT5
    Änderungen V0.9:
        Georeferenzieruzngsmodul
    Änderungen V0.6:
        17.02.17
            - keine Anpassung der Fenstergröße in Abhängigkeit der Dateianzahl,
              da das auf UHD/4K ohnehin nicht passt
            - speichern der letzten Dialoggröße und Wiederherstellung bei Neustart
            - Einbau Resetknopf für Standardvoreinstellungen
            
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
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from qgis.utils import os, sys
    from PyQt5 import QtGui, uic
    from PyQt5.QtWidgets import QApplication,QMessageBox, QDialog, QTableWidgetItem, QDialogButtonBox, QFileDialog
    from PyQt5.QtCore    import QSize, QSettings, QTranslator, qVersion, QCoreApplication, QObject, QEvent

except:
    from PyQt4 import QtGui, uic
    from PyQt4.QtGui import QMessageBox, QDialogButtonBox, QDialog, QTableWidgetItem, QFileDialog
    from PyQt4.QtCore import QSize, QSettings, QTranslator, qVersion, QCoreApplication, QObject, QEvent

import os

try:
    from .fnc4all import *
    from .fnc4ADXF2Shape import *
    from .clsDXFTools import DXFImporter
    from .TransformTools import ReadWldDat
except:
    from fnc4all import *
    from fnc4ADXF2Shape import *
    from clsDXFTools import DXFImporter
    from TransformTools import ReadWldDat



# Programm funktioniert auch ohne installierte gdal-Bibliothek, die Bibo wird nur zur Anzeige der Version genommen
try:
   import gdal
except:
   pass
 
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiADXF2Shape.ui'))


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

class uiADXF2Shape(QDialog, FORM_CLASS):
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
        locale= QSettings().value('locale/userLocale')
        if locale is None or locale == NULL:
            locale = 'en'
        else:
            locale= QSettings().value('locale/userLocale')[0:2]
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

        self.listDXFDatNam.currentRowChanged.connect(self.wld4listDXFDatNam)
        self.chkTransform.clicked.connect(self.chkTransform_clicked) 
        self.optTParam.clicked.connect(self.ManageTransformSettings) 
        self.optTPoint.clicked.connect(self.ManageTransformSettings) 
        
        self.cbTArt.currentIndexChanged.connect(self.ManageTransformFelder4Kombi) 
        
        self.tabTPoints.cellChanged.connect(self.KorrAktTableValue)
        self.leTXOff.editingFinished.connect(self.KorrAktParam_leTXOff)
        self.leTYOff.editingFinished.connect(self.KorrAktParam_leTYOff)
        # self.leTScale.editingFinished.connect(self.KorrAktParam_leTScale) """ Funktion aktuell entfernt
        
        self.optTWld.clicked.connect(self.ManageTransformSettings) 
        self.optTWld.setChecked (True)
        self.cbTArt.addItem(self.tr("1 point (move)"))
        self.cbTArt.addItem(self.tr("2 point (Helmert)"))
        self.cbTArt.addItem(self.tr("3 point (Georef)"))
        self.cbTArt.addItem(self.tr("4 point (Georef)"))
        
        self.btnStart.clicked.connect(self.btnStart_clicked)          
        self.btnReset.clicked.connect(self.btnReset_clicked)  
        
        self.StartHeight = self.height()
        self.StartWidth  = self.width()
        
        self.SetzeVoreinstellungen()
        self.TableNone2Empty(self.tabTPoints)
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
    
    def wld4listDXFDatNam (self):
        if self.chkTransform.isChecked() and self.optTWld.isChecked():
            # nur wenn Worldfile aktiv ist
            if self.listDXFDatNam.currentItem() == None:
                AktDxfDatNam = self.listDXFDatNam.item(0).text()
            else:
                AktDxfDatNam = self.listDXFDatNam.currentItem().text()
            if AktDxfDatNam != self.tr("no DXF-file selected"):
                self.FillPoint4Wld (os.path.splitext(AktDxfDatNam)[0] + ".wld")
    

    def TableNone2Empty( self, tw):
        for row in range(tw.rowCount()):
            for col in range(tw.columnCount()):
                if tw.item(row,col) == None:
                    item = QTableWidgetItem('')
                    tw.setItem(row, col, item)
    
    def FillPoint4Wld (self,wldname):
        self.tabTPoints.setVisible(False)
        if os.path.exists(wldname):
            p1, p2, Fehler = ReadWldDat(wldname)
            if Fehler != None:
                self.lbT4Wld.setText (wldname + ": " + Fehler)
            
            if p1 != None:
                if p2 == None:
                    self.tabTPoints.setRowCount(1)
                else:
                    self.tabTPoints.setRowCount(2)
                self.TableNone2Empty(self.tabTPoints)
                
                self.tabTPoints.setVisible(True)
                self.tabTPoints.item(0,0).setText (str(p1[0][0]));self.tabTPoints.item(0,1).setText (str(p1[0][1]))
                self.tabTPoints.item(0,2).setText (str(p1[1][0]));self.tabTPoints.item(0,3).setText (str(p1[1][1]))                
                if p2 != None:
                    self.tabTPoints.item(1,0).setText (str(p2[0][0]));self.tabTPoints.item(1,1).setText (str(p2[0][1]))
                    self.tabTPoints.item(1,2).setText (str(p2[1][0]));self.tabTPoints.item(1,3).setText (str(p2[1][1]))    
        else:
            self.lbT4Wld.setText (wldname + ": " + self.tr("file not found"))
            
        
    def KorrAktTableValue(self):
        if self.tabTPoints.currentItem() != None:
            if self.tabTPoints.currentItem().text() !="":
                try:
                    dblValue=float(self.tabTPoints.currentItem().text().replace(",","."))
                except:
                    msgbox (self.tr("There is no float value"))
                    dblValue=""
                    self.tabTPoints.scrollToItem(self.tabTPoints.currentItem()) # funktioniert nicht
                self.tabTPoints.currentItem().setText(str(dblValue))

    def KorrAktParam_leTXOff (self):
        if self.leTXOff.text() !="":
            try:
                dblValue=float(self.leTXOff.text().replace(",","."))
            except:
                msgbox (self.tr("There is no float value"))
                dblValue=""
                self.leTXOff.setFocus()
            self.leTXOff.setText(str(dblValue))
    def KorrAktParam_leTYOff (self):
        if self.leTYOff.text() !="":
            try:
                dblValue=float(self.leTYOff.text().replace(",","."))
            except:
                msgbox (self.tr("There is no float value"))
                dblValue=""
                self.leTYOff.setFocus()
            self.leTYOff.setText(str(dblValue))
    """ Funktion aktuell entfernt
    def KorrAktParam_leTScale (self):
        if self.leTScale.text() !="":
            try:
                intValue=int(float(self.leTScale.text().replace(",",".")))
            except:
                msgbox (self.tr("There is no integer value"))
                intValue=""
                self.leTScale.setFocus()
            if intValue==0:
                msgbox (self.tr("scale with zero is not allowed"))
                intValue=""
                self.leTScale.setFocus()           
            self.leTScale.setText(str(intValue))        
    """
    
    def CheckKonstTransWerte(self):
    # Bei Fehler Rückgabe False und Fehlertext
    # sonst True und optional Punktliste p
        Feh = ""
        p=[[],[],[]]
        # 1) Worldfile kontrollieren ---> erfolgt direkt beim Import, da mehrere Dateien (wld's) im Stapel sein können
        if self.optTWld.isChecked():
            return True, None
        
        # 2) Tabellenwerte kontrollieren
        if  self.optTPoint.isChecked():
            # kein Tabellenfeld darf ohne Wert sein
            for row in range(self.tabTPoints.rowCount()):
                for col in range(self.tabTPoints.columnCount()): # 0-3
                    if self.tabTPoints.item(row,col) == None:
                        Feh = "(" + str(row+1) + "," + str(col+1) + ")" + self.tr(" value missing\n")
                        return False, Feh

                    if self.tabTPoints.item(row,col).text().strip() == "":
                        Feh = "(" + str(row+1) + "," + str(col+1) + ")" + self.tr(" value missing\n")
                        return False, Feh
                p[row]=[[float(self.tabTPoints.item(row,0).text()),float(self.tabTPoints.item(row,1).text())],[float(self.tabTPoints.item(row,2).text()),float(self.tabTPoints.item(row,3).text())]]
            # restliche Punkte per Helmert ermitteln
            if self.tabTPoints.rowCount() == 1:
                # Punkte 2 und 3 ermitteln
                p[0], p[1], p[2] = Helmert4Points(p[0], None)
            if self.tabTPoints.rowCount() == 2:
                # Punkt 3 ermitteln
                p[0], p[1], p[2] = Helmert4Points(p[0],p[1])
            return True, p
        
        # 3) (Verschiebungs-) Parameter kontrollieren
        if  self.optTParam.isChecked():
            # Verschiebung immer
            if self.leTXOff.text() == "":
                Feh = Feh  + self.tr("X-Offset - value missing\n")
                return False, Feh
            if self.leTYOff.text() == "":
                Feh = Feh  + self.tr("Y-Offset - value missing\n")  
                return False, Feh

            # beliebige Punkte
            xOffs=float(self.leTXOff.text())
            yOffs=float(self.leTYOff.text())
            p[0]=[[0.0,0.0],[0.0+xOffs,0.0+yOffs]]
            p[1]=[[1000.0,0.0],[1000.0+xOffs,0.0+yOffs]]
            p[2]=[[0.0,1000.0],[0.0+xOffs,1000.0+yOffs]]
            """ aktuell nicht realisiert
            if self.cbTArt.currentIndex() == 1:
                if self.leTScale.text() == "":
                    Feh = Feh  + self.tr("Scale - value missing\n")
            """
            return True, p
        # hier darf der Code nicht rauskommen
        errbox ("Programmierfehler")
    
    def ManageTransformFelder4Kombi(self):
        if  self.optTPoint.isChecked():
            self.tabTPoints.setRowCount(self.cbTArt.currentIndex()+1)
        
        self.lbTScale.setVisible(False) #aktuell nicht realisiert
        self.leTScale.setVisible(False) #aktuell nicht realisiert
        """ aktuell nicht realisiert
        if self.optTParam.isChecked():
            self.lbTScale.setVisible(self.cbTArt.currentIndex() == 1)
            self.leTScale.setVisible(self.cbTArt.currentIndex() == 1)
        """
            
    def ManageTransformSettings(self):
        if self.chkTransform.isChecked():
            self.tabSetting.setTabEnabled(1,True)  # Register aktivieren          
            
            self.tabTPoints.setVisible(self.optTPoint.isChecked() or self.optTWld.isChecked()) # Passpunkttabelle
            self.tabTPoints.setEnabled(self.optTPoint.isChecked())
            
            self.grpTParam.setVisible(self.optTParam.isChecked())  # Parameterliste
            self.cbTArt.setVisible(self.optTPoint.isChecked())     # aktuell nur bei Punkttabelle : (not self.optTWld.isChecked())
            self.lbT4Wld.setVisible(self.optTWld.isChecked())            
            
            
            #self.cbTArt.clear()
            if self.optTParam.isChecked():
                pass
                """aktuell nicht realisiert
                self.cbTArt.addItem(self.tr("Move"))
                self.cbTArt.addItem(self.tr("Move and scale")) aktuell nicht realisiert
                """
            if  self.optTPoint.isChecked():
                self.cbTArt.setCurrentIndex(self.tabTPoints.rowCount()-1)
                
            if  self.optTWld.isChecked():
                # schon mal aktuelle Datei checken (da Ereignis Dateiwechsel fehlt)
                self.wld4listDXFDatNam()
        else:
            # Registerkarte deaktivieren
            self.tabSetting.setTabEnabled(1,False) 


    
    def SetzeVoreinstellungen(self):
        self.ManageTransformSettings()
        
	    # Voreinstellungen setzen
        s = QSettings( "EZUSoft", fncProgKennung() )
        
        # letzte Anzeigegröße wiederherstellen
        SaveWidth  = int(s.value("SaveWidth", "0"))
        SaveHeight = int(s.value("SaveHeight", "0"))
        if SaveWidth > self.minimumWidth() and SaveHeight > self.minimumHeight():
            self.resize(SaveWidth,SaveHeight)

        
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
			
		# 17.02.17: Keine Anpassung mehr, da bei UHD/4K ohnehin  alles anders läuft
        # self.StartHeight=self.height()
        # self.StartMinHeight=self.minimumHeight()
        # Drag & Drop Event
        #if not fncDebugMode():
            # Kommt bei Programmfehleren immer wieder zu komischen Effekten/Abstüzen - deshalb wärend der Entwicklung deaktivieren
            # 23.11.16: D&D deaktiviert, da nicht sichergestellt werden kann, dass alle Dateien aus einem Verzeichnis kommen
            #               und der Anpassungsaufwand im Moment nicht lohnt
            #self.listDXFDatNam.installEventFilter(QLineEditDropHandler(self))
            #self.txtZielPfad.installEventFilter(QLineEditDropHandler(self))

    def chkTransform_clicked(self):
        self.ManageTransformSettings()
        if self.chkTransform.isChecked():
            self.tabSetting.setCurrentIndex(1)
        
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
        s = QSettings( "EZUSoft", fncProgKennung() )
        lastDXFDir = s.value("lastDXFDir", ".")

        MerkAnz=self.listDXFDatNam.count()
        Anz=0
        if myqtVersion == 5:
            AllDXFDatNames=QFileDialog.getOpenFileNames(self, 'Open File', lastDXFDir, 'DXF  (*.dxf)')[0]
        else:
            AllDXFDatNames=QFileDialog.getOpenFileNames(self, 'Open File', lastDXFDir, 'DXF  (*.dxf)')
        for DXFDatName in AllDXFDatNames:
            DXFDatName=(DXFDatName).replace("\\","/")
            if Anz == 0:
                # im Gegensatz zu getOpenFileName() gibt getOpenFileNames Backslash's zurück
                self.listDXFDatNam.clear()
                self.listDXFDatNam.setEnabled(True)     
                (dxfDir, dxfFile) = os.path.split(DXFDatName)
                if (dxfDir != ""):
                    s.setValue("lastDXFDir", dxfDir) 
                #für Übergang    
                #printlog (DXFDatName)
                #self.txtDXFDatNam.setText(DXFDatName)
            Anz=Anz+1        
            self.listDXFDatNam.addItem(DXFDatName) 
            MerkAnz=Anz
        if Anz > 0:
            self.listDXFDatNam.item(0).setSelected(True)
            self.wld4listDXFDatNam()


    def browseZielPfad_clicked(self):
        s = QSettings( "EZUSoft", fncProgKennung() )
        lastSHPDir = s.value("lastSHPDir", ".")
        
        if not os.path.exists(lastSHPDir):
            lastSHPDir=os.getcwd() 

        if myqtVersion == 5:
            flags = QtWidgets.QFileDialog.DontResolveSymlinks | QtWidgets.QFileDialog.ShowDirsOnly
            shpDirName = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory",lastSHPDir,flags)
        else:
            flags = QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly
            shpDirName = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory",lastSHPDir,flags)
        shpDirName=shpDirName.replace("\\","/")
        self.txtZielPfad.setText(shpDirName)

        if shpDirName != "":
            s.setValue("lastSHPDir", shpDirName)
    
    def OptSpeichern(self):        
        s = QSettings( "EZUSoft", fncProgKennung() )
        s.setValue( "bGenCol", "Ja" if self.chkCol.isChecked() == True else "Nein")
        s.setValue( "bGenLay", "Ja" if self.chkLay.isChecked() == True else "Nein")
        s.setValue( "bGenSHP", "Ja" if self.chkSHP.isChecked() == True else "Nein")
        s.setValue( "bFormatText", "Ja" if self.chkUseTextFormat.isChecked() == True else "Nein")
        s.setValue( "bUseColor4Point", "Ja" if self.chkUseColor4Point.isChecked() == True else "Nein")
        s.setValue( "bUseColor4Line", "Ja" if self.chkUseColor4Line.isChecked() == True else "Nein")
        s.setValue( "bUseColor4Poly", "Ja" if self.chkUseColor4Poly.isChecked() == True else "Nein")
        
        s.setValue( "iCodePage", self.cbCharSet.currentIndex())
         
    
    def btnReset_clicked(self):
        result = QMessageBox.question(None,'Another DXF2Shape' , self.tr('Restore default settings'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)        
        if result == QMessageBox.Yes:
            QSettings( "EZUSoft", fncProgKennung() ).clear()
            self.resize(self.StartWidth,self.StartHeight)
            self.SetzeVoreinstellungen()
    
    def btnStart_clicked(self):
        # 0. Test ob eine DXF gewählt
        if self.listDXFDatNam.count() == 0 or (self.listDXFDatNam.count() == 1 and self.listDXFDatNam.item(0).text() == self.listEmpty):
            QMessageBox.critical(None,  self.tr("Please specify a DXF-File"),self.tr(u"DXF-file not selected")) 
            return

        # 1. Test ob alle dxf lesbar
        #allDXFDat = self.listDXFDatNam('', Qt.MatchRegExp)
        for i in range(self.listDXFDatNam.count()):
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
        if ZielPfad[:-1] != "/" and ZielPfad[:-1] != "\\":
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
            
        #4. Test ob allgemeine Transformationswerte korrekt
        if self.chkTransform.isChecked():
            # Bei Fehler Rückgabe False und Fehlertext
            # sonst True und optional Punktliste p
            Korrekt, DreiPassPunkte=self.CheckKonstTransWerte()
            if not Korrekt:
                errbox (DreiPassPunkte)
                self.tabSetting.setCurrentIndex(1) # registerkarte aktivieren
                return
        else:
            DreiPassPunkte=None
            
        self.OptSpeichern()
        self.tabSetting.setCurrentIndex(0) # erste Registerkarte, damit Laufbalken sichtbar
        
        Antw = DXFImporter (self, self.listDXFDatNam, ZielPfad, self.chkSHP.isChecked(), self.cbCharSet.currentText(),self.chkCol.isChecked(),self.chkLay.isChecked(), self.chkUseTextFormat.isChecked(), self.chkUseColor4Point.isChecked(), self.chkUseColor4Line.isChecked(), self.chkUseColor4Poly.isChecked(), dblFaktor, self.chkTransform.isChecked(), DreiPassPunkte)
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
        Anz(self.btnReset)
        Anz(self.cbCharSet)
        Anz(self.button_box.button(QDialogButtonBox.Close))
        Anz(self.browseDXFDatei);Anz(self.browseZielPfad)
        Anz(self.listDXFDatNam);Anz(self.txtZielPfad)
        Anz(self.chkCol); Anz(self.chkLay); Anz(self.chkSHP)
        Anz(self.lbFaktor);Anz(self.txtFaktor)
        
        Anz(self.chkTransform)
        Anz(self.tabSetting)


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
        s = QSettings( "EZUSoft", fncProgKennung() )
        s.setValue("SaveWidth", str(self.width()))
        s.setValue("SaveHeight", str(self.height()))
if __name__ == "__main__":
 
    app = QApplication(sys.argv)
    #from uiADXF2Shape import uiADXF2Shape
    QFileDialog.getOpenFileNames(self, 'Open File', "", 'DXF  (*.dxf)')
    #window = uiADXF2Shape()
    #window.show()
    #sys.exit(app.exec_())
    #"""


# -*- coding: utf-8 -*-
"""
  13.02.2018: fncDebugMode musste hier raus, da in Projektdatei definiert
  26.01.2018: alle PlugIn's abgeglichen

/***************************************************************************
 fnc4all: Gemeinsame Basis für QGIS2 und QGIS3
                                 A QGIS plugin
 CAIGOS-PostgreSQL/PostGIS in QGIS darstellen
                              -------------------
        begin                : 2016-04-18
        git sha              : $Format:%H$
        copyright            : (C) 2016 by EZUSoft
        email                : qgis (at) makobo.de
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
# Einbau in QGIS per
# >> sys.path.append('C:/Users/.../.qgis3/python/plugins/<plugin-name>')
# >> sys.path.append('C:/Users/.../AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/GermanyCadastralParcels')
# >> from fnc4all import *
# Aktualisierung python 3.x per
# >> import importlib
# >> importlib.reload(fnc4all)

from qgis.core import *
from qgis.utils import os, sys
from itertools import cycle

try:
    from PyQt5 import QtGui
    from PyQt5.QtCore import QSettings
    from PyQt5.QtWidgets import QApplication,QMessageBox

    def myQGIS_VERSION_INT():
        return Qgis.QGIS_VERSION_INT
    myqtVersion = 5

except:
    from PyQt4 import QtGui
    from PyQt4.QtCore import QSettings
    from PyQt4.QtGui import QMessageBox,QApplication
    def myQGIS_VERSION_INT():
        return QGis.QGIS_VERSION_INT
    myqtVersion = 4

# es kommt (verumtlich bei gemischten Installationen) vor, dass QString nicht verfügbar
try:
    from PyQt4.QtCore import QString
except ImportError:
    QString = type(str)
    
    
import re
import time 
import os
import getpass
import traceback
import tempfile
import codecs
from glob import glob

######################### QGIS TreeNode Handling ################################
def NodeFindByFullName (FullNode, Start = None):
    if Start is None: Start=QgsProject.instance().layerTreeRoot()
    if type(FullNode) == type([]):
        sNode=FullNode
    else:
        sNode=FullNode.split("\t")
    Gefunden=None
    for node in Start.children():
        if str(type(node))  == "<class 'qgis._core.QgsLayerTreeGroup'>":
            if node.name() == sNode[0]:
                if len(sNode) > 1:
                    Gefunden = NodeFindByFullName(sNode[1:], node)
                else:
                    Gefunden = node
    return Gefunden             


def NodeCreateByFullName (FullNode, Start = None):
    # Rückgabewerte:
    #   1.) Der Knoten
    #   2.) Anzahl der neu angelegten Gruppen
    ToDo=0
    if Start is None: Start=QgsProject.instance().layerTreeRoot()
    if type(FullNode) == type([]):
        sNode=FullNode
    else:
        sNode=FullNode.split("\t")
    Found=False
    for node in Start.children():
        if str(type(node))  == "<class 'qgis._core.QgsLayerTreeGroup'>":
            if node.name() == sNode[0]: 
                Found=True
                break
    if not Found: node=Start.addGroup(sNode[0]);ToDo=ToDo+1
    if len(sNode) > 1:
        node, ReToDo = NodeCreateByFullName (sNode[1:],node)
        ToDo=ToDo+ReToDo
    return node, ToDo

def NodeRemoveByFullName (FullNode, Start = None):
    if Start is None: Start=QgsProject.instance().layerTreeRoot()
    if type(FullNode) == type([]):
        sNode=FullNode
    else:
        sNode=FullNode.split("\t")
    delNodeName=sNode[-1:][0]
    if len(sNode) > 1:
        parent=NodeFindByFullName (sNode[:-1],Start)
    else:
        parent=Start
    if not parent: return False
    for node in parent.children():
        if str(type(node))  == "<class 'qgis._core.QgsLayerTreeGroup'>":
            if node.name() == delNodeName:
                parent.removeChildNode(node)
                return True
######################### QGIS TreeNode Handling ################################

def toUnicode(text):
    # Python2 erzeugt           <type 'unicode'>
    # Python3 erzeugt (bleibt)  <class 'str'>
    # QT4 hat Typ QString
    # https://stackoverflow.com/questions/18404546/set-up-notepad-and-nppexec-to-print-unicode-characters-from-python
    # für die saube Ausgabe an die (Notepad++ - Console) env_set PYTHONIOENCODING=utf-8
    if myqtVersion == 4 and type(text) == QString:
        return unicode(text)
    if (type(text) == str and sys.version[0] == "2"):
        return text.decode("utf8")
    else:
        return text
    
glFehlerListe=[]
glHinweisListe=[]
def addFehler (Fehler): 
    glFehlerListe.append (toUnicode(Fehler))
def getFehler() :
    return glFehlerListe
def resetFehler() :
    global glFehlerListe
    glFehlerListe = []  
def addHinweis (Hinweis):
    glHinweisListe.append (toUnicode(Hinweis))
def getHinweis2String() :
    try:
        return u"\n".join(glHinweisListe)
    except:
        return "\n".join(glHinweisListe)
        #return "Unicode fehler"
def getHinweis() :
    return glHinweisListe
def resetHinweis() :
    global glHinweisListe
    glHinweisListe = [] 


# unerwarteter LZF mit Sofortmeldung
""" Aufruf per:
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    subLZF ("Irgendwas")
"""
def subLZF(Sonstiges = None):
    #http://stackoverflow.com/questions/1278705/python-when-i-catch-an-exception-how-do-i-get-the-type-file-and-line-number
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    tb_lineno=exc_tb.tb_lineno
    try:
        QgsMessageLog.logMessage( traceback.format_exc().replace("\n",chr(9))+ (chr(9) + Sonstiges if Sonstiges else ""), u'EZUSoft:Error' )
    except:
        pass
#    if fncDebugMode():
#        QMessageBox.critical( None,tr("PlugIn Error") ,str(exc_type) + ": \nDatei: " + fname + "\nZeile: "+ str(tb_lineno) + ("\n" + Sonstiges if Sonstiges else ""))
    addFehler ("LZF:" + traceback.format_exc().replace("\n",chr(9)) + (chr(9) + Sonstiges if Sonstiges else ""))    

def cut4view (fulltext,zeichen=1500,zeilen=15,anhang='\n\n                  ............. and many more .........\n'):
    cut = False
    ctext=fulltext
    if len(fulltext) > zeichen:
        cut=True
        ctext=ctext[:zeichen]
    
    arr=ctext.split('\n')
    if len(arr) > zeilen:
        cut = True
        ctext= '\n'.join(arr[:zeilen])
    if cut:
        ctext=ctext + anhang
    return ctext
 
def errbox (text,p=None):
    su= toUnicode(text)

    QMessageBox.critical(None, "PlugIn Error", cut4view(su))
    try:
        QgsMessageLog.logMessage( su, u'EZUSoft:Error' )
    except:
        pass


def msgbox (text):
    su= toUnicode(text)

    QMessageBox.information(None, "PlugIn Hinweis", cut4view(su))
    try:
        QgsMessageLog.logMessage( su, u'EZUSoft:Hinweise' )
    except:
        pass

def errlog(text, DebugMode = False):
    su= toUnicode(text)   
    if DebugMode:
        QMessageBox.information(None, "DEBUG:", su)
    
    try:
        QgsMessageLog.logMessage( su, u'EZUSoft:Fehler' )
    except:
        pass

def EZUTempClear(All=None):
    Feh=0
    Loe=0
    tmp=EZUTempDir()
    if All:
        for dat in glob(tmp +'*.*'):
            try:
                os.remove(dat)
                Loe+=1
            except:
                Feh+=1
    else:
        for shp in glob(tmp +'*.shp'):
            try:
                os.remove(shp)
                Loe+=1
                for rest in glob(shp[0:-4] + '.*'):
                    os.remove(rest)
                    Loe+=1
            except:
                Feh+=1
                
    return Loe, Feh
    #QMessageBox.critical(None, "Leeren", tmp)

def EZUTempDir():
    # 28.06.16 Replce() eingefügt, da processing.runalg sehr empfindlich hinsichtlich Dateinamen ist
    tmp=(tempfile.gettempdir()).replace("\\","/") + "/{D5E6A1F8-392F-4241-A0BD-5CED09CFABC7}/"
    if not os.path.exists(tmp):
        os.makedirs(tmp) 
    if os.path.exists(tmp):
        return tmp
    else:
        QMessageBox.critical(None,tr("Program termination"), tr("Temporary directory\n%s\ncan not be created")%tmp)
        return None

def debuglog(text,DebugMode=False):
    if DebugMode:
        su= toUnicode(text)   
        try:
            QgsMessageLog.logMessage( su, 'EZUSoft:Debug' )
        except:
            pass

def hinweislog(text,p=None):
        su= toUnicode(text)   
        try:
            QgsMessageLog.logMessage( su, 'AXF2Shape:Comments' )
        except:
            pass
    
def printlog(text,p=None):
    su= toUnicode(text)        
    try:
        print (su)
    except:
        try:
            print (su.encode("utf-8"))
        except:
            print (tr("printlog:Tip can not view"))

def fncKorrDateiName (OrgName,Ersatz="_"):
    NeuTex=""
    for i in range(len(OrgName)):
        if re.search("[/\\\[\]:*?|!=]",OrgName[i]):
            NeuTex=NeuTex+Ersatz
        else:
            NeuTex=NeuTex+OrgName[i]
    return NeuTex      
    
def fncDateCode():
    lt = time.localtime()
    return ("%02i%02i%02i") % (lt[0:3])  

def fncXOR(message, key=None):
    if key==None:
        key=fncDateCode()
    return  ''.join(("%0.1X" % (ord(c)^ord(k))).zfill(2) for c,k in zip(message, cycle(key)))


def ifAscii(uText):
    try:
        for char in uText:
            if(ord(char))> 128:
              return False   
        return True
    except:
        return False 
    
def toUTF8(uText):
    # 06.10.2016:
    # Diese Funktion ist die Lösung für ein ganz übles Problem
    # Beim Auslesen der PG-Datenbank kommt es zufällig und nicht wiederholbar zu Problemen mit Umlauten (UniCode)
    # Aus unersichtlichen Gründen wird manchmal kein Ansiwert sondern UTF-8 übergeben
    # z.B: STPL-F_FussgÃ¤ngerzone, STPL-T_StraÃenbahnLinie,STPL-T_FÃ¶rderschule50000
    #
    # da hier bei der Ausgabe auch die jeweilige Console eine Rolle spielt, konnte die Ursache 
    # nicht gefunden werden
    try:
        a=""
        for char in uText:
            a= a + chr(ord(char))
        return a.decode("utf8")
    except:
        return uText    
        
def tryDecode(txt,sCharset):
    try:
        re=txt.decode( sCharset) 
        return re
    except:
        return '#decodeerror#'    

def ClearDir(Verz):
    for dat in glob(Verz +'*.*'):
        try:
            os.remove(dat)
        except:
            return False
    return True
    
def fncMakeDatName (OrgName):
    v=OrgName.replace("\\","/")
    return v.replace("//","/")

def qXDatAbsolute2Relativ(tmpDat, qlrDat, PathAbsolute):
        # Absolute Pfade eine QRL/QGS in relative umschreiben
        # bei Layern sucht zwar QGIS automatisch relativ wenn absolute fehlt, bei svg allerdings nicht
        subPath=fncMakeDatName(PathAbsolute + "/") # encode('ascii') 4 Phython3
        iDatNum = open(tmpDat)
        oDatNum = open(qlrDat,"w")
        for iZeile in iDatNum:
            s1=iZeile.replace('source="' + subPath,'source="./') # Datenquellen
            s1=s1.replace('k="name" v="' + subPath,'k="name" v="./') # svg-Dateien
            s1=s1.replace('<datasource>' + subPath,'<datasource>./') # Datenquellen
            oDatNum.write(s1)
        iDatNum.close()
        oDatNum.close()
        os.remove(tmpDat)
        
if __name__ == "__main__": 
    fncMakeDatName("abc")
    #tmpDat="X:/Downloaddienst/FnP/FnP-2.Entwurf.qlr"
    #qlrDat="D:/tar/2.qlr"
    #s="D:/Downloaddienst/FnP/"
    #qXDatAbsolute2Relativ (tmpDat,qlrDat,s)
    #app = QApplication(sys.argv)
    #msgbox (u"Es wurden keine Ebenen zur Darstellung  ausgewählt")
    #app = QApplication(sys.argv)
    #if myQGIS_VERSION_INT ()  < 21200:
    #    print (myQGIS_VERSION_INT())    
    #print (fncBrowserID())

    #addHinweis(u"ähgfhgiuq")
    #addHinweis("ähgfhgiuq")
    #msgbox("\n".join(getHinweis()))

# -*- coding: utf-8 -*-
"""
    Stand 13.03.17
        -Problem QGIS 2.8 beseitigt (from qgis.core import QgsMessageLog, QCoreApplication)
    Stand 03.03.17
        - Texte der Ausgabeboxen auf  beschränkt
/***************************************************************************
 fnc4all
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
from itertools import cycle, izip
from PyQt4.QtGui import QMessageBox,QApplication
from qgis.core import *
#from qgis.core import QgsMessageLog, QCoreApplication
import re
import time 
import os
import getpass
import traceback
import tempfile
from glob import glob

def tr( message):
    """Get the translation for a string using Qt translation API.

    We implement this ourselves since we do not inherit QObject.

    :param message: String for translation.
    :type message: str, QString

    :returns: Translated version of message.
    :rtype: QString
    """
    # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
    return QCoreApplication.translate('clsDXFTools', message)
    
def fncDebugMode(): 
    return False
    
glFehlerListe=[]
glHinweisListe=[]
def addFehler (Fehler): 
    glFehlerListe.append (Fehler)
def getFehler() :
    return glFehlerListe
def resetFehler() :
    global glFehlerListe
    glFehlerListe = []  
def addHinweis (Hinweis):
    glHinweisListe.append (Hinweis)
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
    if fncDebugMode():
        QMessageBox.critical( None,tr("PlugIn Error") ,str(exc_type) + ": \nDatei: " + fname + "\nZeile: "+ str(tb_lineno) + ("\n" + Sonstiges if Sonstiges else ""))
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
    su=text
    if type(text) == str:
        su=text.decode("utf8")

    QMessageBox.critical(None, "PlugIn Error", cut4view(su))
    try:
        QgsMessageLog.logMessage( su, u'EZUSoft:Error' )
    except:
        pass


def msgbox (text):
    su=text
    if type(text) == str:
        su=text.decode("utf8") 
    
    QMessageBox.information(None, "PlugIn Hinweis", cut4view(su))
    try:
        QgsMessageLog.logMessage( su, u'EZUSoft:Hinweise' )
    except:
        pass

def errlog(text,p=None):
    su=text
    if type(text) == str:
        su=text.decode("utf8")   
    if fncDebugMode():
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

def debuglog(text,p=None):
    if fncDebugMode():
        su=text
        if type(text) == str:
            su=text.decode("utf8")   
        try:
            QgsMessageLog.logMessage( su, 'EZUSoft:Debug' )
        except:
            pass

def hinweislog(text,p=None):
        su=text
        if type(text) == str:
            su=text.decode("utf8")   
        try:
            QgsMessageLog.logMessage( su, 'AXF2Shape:Comments' )
        except:
            pass
def fncBrowserID():
    s = QSettings( "EZUSoft", "ADXF2Shape" )
    s.setValue( "-id-", fncXOR(("ADXF2ShapeID=%02i%02i%02i%02i%02i%02i") % (time.localtime()[0:6])) )
    return s.value( "–id–", "" ) 
    
def printlog(text,p=None):
    su=text
    if type(text) == str:
        su=text.decode("utf8")        
    try:
        print su
    except:
        try:
            print su.encode("utf-8")
        except:
            print tr("printlog:Tip can not view")

def fncKorrDateiName (OrgName,Ersatz="_"):
    NeuTex=""
    for i in range(len(OrgName)):
        if re.search("[/\\\[\]:*?|<>]",OrgName[i]):
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
    return  ''.join(("%0.1X" % (ord(c)^ord(k))).zfill(2) for c,k in izip(message, cycle(key)))

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

if __name__ == "__main__":
    print cut4view('1\n\n2\n3\n4',1000,2)
    dummy=1





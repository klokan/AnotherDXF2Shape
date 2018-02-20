# -*- coding: utf-8 -*-
"""
  09.01.2018: alle PlugIn's abgeglichen

/***************************************************************************
 fnc4CaigosConnector: Gemeinsame Basis für QGIS2 und QGIS3
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
try:
    from fnc4all import *

except:
    from .fnc4all import *


def fncProgKennung():
    return "CAIGOS-Konnektor" + str(myqtVersion)

def fncProgVersion():
    return "V 1.01"
    
def fncDebugMode(): 
    return True

def fncBrowserID():
    s = QSettings( "EZUSoft", fncProgKennung() )
    s.setValue( "-id-", fncXOR((fncProgKennung() + "ID=%02i%02i%02i%02i%02i%02i") % (time.localtime()[0:6])) )
    return s.value( "–id–", "" ) 
    
def tr( message):
    return message  # hier braucht es keine Übersetzung
    
def fncCGFensterTitel(intCG = None):
    s = QSettings( "EZUSoft", fncProgKennung() )
    sVersion = "-"
    if not intCG :
        intCG = int(s.value( "cgversion",-1))
    if intCG == 0:
        sVersion = "11.2"
    if intCG == 1:        
        sVersion = "2016"
    return u"CAIGOS Importer für Version " + sVersion + "   (Programmversion " + fncProgVersion() + ")" 
    
if __name__ == "__main__": 
    print (fncCGFensterTitel())
    pass





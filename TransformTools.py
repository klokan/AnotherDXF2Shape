# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TransformTools
                                 A QGIS plugin
 KonverDXF to shape and add to QGIS
                              -------------------
        begin                : 2017-09-20 V0.9
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
    from .fnc4all import *
except:
    from fnc4all  import *
    
from copy import deepcopy
import math

def tr(message):
    return QCoreApplication.translate('@default', message)
        
def ReadWldDat(wldname):
    # http://desktop.arcgis.com/de/arcmap/10.3/manage-data/cad/world-files-for-cad-datasets.htm
    # 25933.063000,9032.704720 1702332.110159,309622.102491
    # ein oder zwei Passpunkte - ein oder 2 Zeilen
    p1=None;p2=None;Fehler=None
    try:
        if not os.path.exists(wldname):
            Fehler = tr("file not found")
            return None, None, Fehler
        zNum = 0;pNum = 0; bOk=False
        fWldDat  = open(wldname, "r")
        for Zeile in fWldDat:
            zNum+=1
            Zeile=Zeile.strip() # Zeilenende entfernen
            if Zeile != "": # Leerzeilen ignorieren
                pNum+=1
                Zeile=Zeile.replace("\t"," ") # sicherheitshalber eigentlich ist tab nicht definiert
                Zeile=Zeile.replace(", ",",");Zeile=Zeile.replace(" ,",",") # überflüssige Leerzeichen

                paare = Zeile.split(" ")
                if len(paare) != 2:
                    Fehler = tr("wrong syntax in line: ") + str(zNum)
                    return None, None, Fehler                
                qKoo=paare[0].split(",")
                if len(qKoo) != 2:
                    Fehler = tr("wrong 'From' syntax in line: ") + str(zNum)
                    return None, None, Fehler 
                zKoo=paare[1].split(",")
                if len(zKoo) != 2:
                    Fehler = tr("wrong 'To' syntax in line: ") + str(zNum)
                    return None, None, Fehler
                
                # alle Koordinaten auf Double Checken
                for d in [qKoo[0],qKoo[1],zKoo[0],zKoo[1]]:
                    try:
                        d =float(d)
                    except:
                        Fehler = d + tr(": no float value")
                        return None, None, Fehler
                
                if pNum == 1: p1 = [float(qKoo[0]),float(qKoo[1])],[float(zKoo[0]),float(zKoo[1])]
                if pNum == 2: p2 = [float(qKoo[0]),float(qKoo[1])],[float(zKoo[0]),float(zKoo[1])]
                
                
                if pNum > 2:
                    Fehler = tr("more than 2 lines/pairs of points")
                    return p1,p2,Fehler
        fWldDat.close()
        if pNum==0:
            Fehler = tr("no lines/pairs of points")
            return p1,p2,Fehler
    except:
        p1=None;p2=None
        subLZF (tr("file not correct"))
    
    return p1,p2,Fehler
    
def Helmert4Points (p1,p2):
    def WinSysToGeo (BogMass):
        # Umwandlung rad -> gon
        Pi = math.atan(1) * 4
        return 200 / Pi * BogMass
    def MittelWert (pArr):
        xS=0;yS=0
        for p in pArr:
            xS = xS + p[0]; yS = yS + p[1]
        return xS/2, yS/2
    def sumQS_xy (KooArray1, xS1 , KooArray2, yS2):
        erg = 0.0
        for i in range (len(KooArray1)):
            erg = erg + ((xS1 - KooArray1[i][0]) ** 2 + (yS2 - KooArray1[i][1]) ** 2)
        return erg
    def sumP_x(KooArray1, xS1, KooArray2, xS2):
        erg = 0.0
        for i in range (len(KooArray1)):
            erg = erg + ((xS1 - KooArray1[i][0]) * (xS2 - KooArray2[i][0]))
        return erg
    def sumP_y(KooArray1, yS1, KooArray2, yS2):
        erg = 0.0
        for i in range (len(KooArray1)):
            erg = erg + ((yS1 - KooArray1[i][1]) * (yS2 - KooArray2[i][1]))
        return erg
    def sumP_xy(KooArray1, xS1, KooArray2, yS2):
        erg = 0.0
        for i in range (len(KooArray1)):
            erg = erg + ((KooArray1[i][0] - -xS1) * (KooArray2[i][1] - yS2))
        return erg
    def Max_xy(KooArray):
        maxX = KooArray[0][0];maxY = KooArray[0][1]
        for i in range (len(KooArray)):
            if(KooArray[i][0] > maxX):
                maxX=KooArray[i][0]
            if(KooArray[i][1] > maxY):
                maxY=KooArray[i][1]
        return maxX, maxY        
       
    if p2==None:
        # einfache Verschiebung
        p2=deepcopy(p1) ;p3=deepcopy(p1)
        p2[0][0] = p1[0][0] + 1000.0; p2[1][0] = p1[1][0]+1000.0
        p3[0][1] = p1[0][1] + 1000.0; p2[1][1] = p1[1][1]+1000.0
    else:
        # jetzt richtige Transformation
        qKooArray = [p1[0],p2[0]]
        zKooArray = [p1[1],p2[1]]
        maxX,maxY=Max_xy(qKooArray)
        p3=[maxX+1000.0,maxY+1000.0],[0.0,0.0]

        qXs, qYs = MittelWert (qKooArray) # für Quelle
        zXs, zYs = MittelWert (zKooArray) # für Ziel
        WI   = sumQS_xy([p1[0],p2[0]],qXs,[p1[0],p2[0]],qYs)
        WII  = sumP_x(zKooArray, zXs, qKooArray, qXs) + sumP_y(zKooArray, zYs, qKooArray, qYs)
        WIII = sumP_xy(qKooArray, qXs, zKooArray, zYs) - sumP_xy(zKooArray, zYs, qKooArray, qYs)
        a1 = WII / WI
        b1 = WIII / WI
        win   = WinSysToGeo(math.atan(b1 / a1))
        masst = math.sqrt(a1 ** 2 + b1 ** 2)
        dX = zXs - a1 * qXs + b1 * qYs
        dY = zYs - a1 * qYs - b1 * qXs
        #print dX, dY, a1, b1, masst, win
        p3[1][0] = dX + a1 * p3[0][0] - b1 * p3[0][1]
        p3[1][1] = dY + p3[0][0] * b1 + p3[0][1] * a1
        #print p3
        #return dX, dY, masst, win
    return p1, p2, p3


if __name__ == "__main__":
    app = QApplication(sys.argv)
    p1, p2, Fehler = ReadWldDat (u"X:/Beckus/2DG_20170914_145454.wld")
    if p1 != None:
        p1, p2, p3 = Helmert4Points(p1, p2)
        #print "p1",p1
        #print "p2",p2
        #print "p3",p3
    if Fehler != None:
        errbox (Fehler)
    if len(getFehler()) > 0:
        errbox("\n\n".join(getFehler()))
        resetFehler()
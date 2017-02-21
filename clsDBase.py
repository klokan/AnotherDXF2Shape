# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsDBase
    Änderungen V0.7:
        21.02.17 
            - Kodierungsprobleme beseitigt
        13.12.16
            - Ersterstellung
            
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

from osgeo import ogr
from PyQt4.QtCore import  QCoreApplication
from fnc4all import *
import locale

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
    
def ZahlTextSplit(zt):
    z=""
    t=""
    isText = False
    for c in zt:
        if not c in "01234567890.":
            isText=True
        if isText:
            t=t+c
        else:
            z=z+c
    return float(z),t    

def fnctxtOGRtoQGIS(cArt):
    if cArt == 1:
        return 2
    if cArt == 2:
        return 1
    if cArt == 3:
        return 0
    if cArt == 4:
        return 5
    if cArt == 5:
        return 4
    if cArt == 6:
        return 3
    if cArt == 7:
        return 8
    if cArt == 8:
        return 7 
    if cArt == 9:
        return 6 
    # 10-13 (ganz unten) ist mit QGIS nicht darstellbar, deshalb auf unten setzen
    if cArt == 10:
        return 2 
    if cArt == 11:
        return 1 
    if cArt == 12:
        return 0  
        
def trennArtDaten(ArtDaten):
    #BRUSH(fc:#dcdcdc)
    #LABEL(f:"Arial",t:"{\fArial|b1|i0|c0|p34;VZOG}",s:3.5g,p:8,c:#ff7f7f)
    sDaten = ""
    sArt = ""
    inDaten = False
    for c in ArtDaten[:-1]:
        if c == '(' and not inDaten:
            inDaten = True
            c = ''
        if inDaten:
            sDaten = sDaten + c
        else:
            sArt = sArt + c
    return sArt, sDaten
    
def csvSplit(csvZeile, trenn=',', tKenn='"', tKennDel = True):
    #csvZeile: Datenzeile 
    #trenn:    Feldtrenner
    #tKenn:    Textkennzeichen
    
    #Trenner innerhalb von Freitexten ersetzen

    inString = False
    mask = ""
    s = ''
    sb = False
    for c in csvZeile: 

        if c == tKenn and not sb:
            inString = not inString
        if c == trenn and inString  and not sb:
            if mask == "":
                mask = "$$"
                while mask in csvZeile:
                    mask = mask + '$'
            s=s+mask
        else:
            if not (tKennDel and (not sb) and c == tKenn): 
                s=s+c
        if c == "\\":
            sb = True
        else:
            sb = False
            
    arr = s.split(trenn)
    if mask <> "":
        for i in range(0,len(arr)):
            arr[i] = arr[i].replace(mask,trenn)

    return arr
    

def splitText (fText,TxtType):
    #http://docs.autodesk.com/ACD/2010/ENU/AutoCAD%202010%20User%20Documentation/index.html?url=WS1a9193826455f5ffa23ce210c4a30acaf-63b9.htm,topicNumber=d0e123454
    # V1: %%u1106                               # TEXT  unterstrichender Text aus Caigos
    # V2: {\fArial|b0|i1|c0|p34;\L151}          # MTEXT unterstrichender Text  vom LVA
    # V3: \fTimes New Roman|i1|b0;Rue Presles   # MTEXT Datei PONT A CELLES 2010.dxf von pierre.mariemont
    # V4: \S558/15;                             # MTEXT komplette gebrochene Flurstücksnummer (Geograf)
    # ob Text oder MTEXT kann im Moment nicht immer unterschieden werden
    
    underline = False
    bs = False
    uText = r""
    ignor = False
    font = ""
    delSemi = False
    inFont = False
    aktText=fText
    FlNum = False
    if TxtType == "TEXT" or TxtType == "UNDEF":
        # 1. Formatierungen TEXT
        #    Die Codes sind nirgends definiert
        # %%u entfernen und ggf. underline setzen
        if "%%u" in aktText:
            underline=True
            aktText = aktText.replace('%%u','')
        # %%c ist Ø
        aktText = aktText.replace('%%c','Ø') # geht nur bei Unicode als Zeichensatz, hier muss noch irgendwas getan werden
    
    if TxtType == "MTEXT" or TxtType == "UNDEF":
        # 2. Formatierungen MTEXT
        for c in aktText:
            # Kennungen mit nachfolgendem Zeichen, welche OGR  nicht auswertet
            if bs and c.upper() == 'O': # ignorieren Overline on/off
                c=''
                ignor = True
            if bs and c.upper() == 'L': # underline on/off: only for all
                c=''
                underline = True
                ignor = True
            if bs and c == 'S': # Stacks the subsequent text at the /, #, or ^ symbol: aktuell nur \S und Semikolon entfernen
                c=''
                ignor = True
                delSemi = True
                FlNum = True

            if bs and c.upper() == 'F': # \Ffont name; Changes to the specified font file 
                ignor = True
                inFont = True 
                delSemi = True
            if c == ';' and delSemi:
                c= ''
                inFont=False
                delSemi = False
            # filtert OGR bereits
            #if bs and c.upper() == '~': # nonbreaking space: to space
            #    c=' '
            #    ignor = True
            #if bs and c == 'P': # Ends paragraph: to \n
            #    c='\n'
            #    ignor = True    
            
            if not bs and (c == '{' or c == '}'): # nur für Formatierung
                c = ''
            else:
                ignor = True
            if c == '\\':
                bs = True
            else:
                if not ignor:
                    if bs:
                        uText = uText + '\\'
                if inFont:
                    font = font + c
                else:
                    uText = uText  + c
                bs = False
            ignor = False
        aktText = uText
    return aktText, underline, font, FlNum
 
#print splitText(r'%%u1144',"TEXT")    

def DBFedit (shpdat,bFormat,sCharSet):
    if sCharSet == "System":
        sCharSet=locale.getdefaultlocale()[1]

    source = ogr.Open(shpdat, update=True)
    if source is None:
        addFehler(tr('ogr: can not open: ') + shpdat)
        return
    layer = source.GetLayer()
    laydef = layer.GetLayerDefn()
    
    Found = False
    for i in range(laydef.GetFieldCount()):
        if laydef.GetFieldDefn(i).GetName() == 'ogr_style':
            Found = True

    if not Found:
        addFehler(tr("missing field 'ogr_style': ") + shpdat)
        return
    

    # scheinbar nur 10 Zeichen bei Feldnamen erlabt
    layer.CreateField(ogr.FieldDefn('font', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('angle', ogr.OFTReal))    
    layer.CreateField(ogr.FieldDefn('size', ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn('size_u', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('anchor', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('color', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('underline', ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn('plaintext', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('fcolor', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('flnum', ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn('bold', ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn('italic', ogr.OFTInteger))

    i=1
    feature = layer.GetNextFeature()
    while feature:
        #try:
            TxtType = "UNDEF"
            SubClass = feature.GetField('SubClasses')
            if SubClass is None:
                addHinweis(tr("missing field 'SubClasses' in: ") + shpdat)
            else:
                # AcDbEntity:AcDbMText
                # AcDbEntity:AcDbText:AcDbText
                if SubClass.find("AcDbMText")>=0:
                    TxtType = "MTEXT" 
                if SubClass.find("AcDbText")>=0:
                    TxtType = "TEXT"
            att=feature.GetField('ogr_style') #http://www.gdal.org/ogr_feature_style.html
            if att is None:
                addHinweis(tr("missing field 'ogr_style' in: ") + shpdat)
            else:
                sArt,sDaten = trennArtDaten(att)
                #if att[:6] == "LABEL(":
                    #LABEL(f:"Arial",t:"%%c 0,40m",a:11,s:0.5g,c:#000000)
                    #print att

                params = csvSplit (sDaten)
                for param in params:
                    arr=csvSplit(param,":")
                    if len(arr) == 2:
                        f = arr[0]
                        w = arr[1]
                        #print str(sArt),str(f),str(w)
                        if f == "c":
                            feature.SetField('color', w)
                        if f == "fc":
                            # Schwarz als Füllung mach meist keinen Sinn
                            if w == "#000000": w="#ffffff"
                            feature.SetField('fcolor', w)
                        if f == "f":
                            feature.SetField('font', w)
                        if f == "a":
                            dWin = float(w)
                            if dWin >=360:
                                dWin = dWin - 360 # ogr bringt teilweise Winkel von 360 Grad, was funktioniert, aber verwirrt                               
                            feature.SetField('angle', dWin)
                        if f == "p":
                            if sArt == "LABEL":
                                feature.SetField('anchor', fnctxtOGRtoQGIS(int(w)))
                        if f == "s":
                            z,t=ZahlTextSplit(w)
                            # Size_u wird im Moment nicht weiter ausgewertet,
                            # da bei DXF wohl nur g = Karteneinheiten möglich
                            feature.SetField('size', z)
                            feature.SetField('size_u', t)
                        if f == "t":
                            # den eigentlichen Text, doch besser aus der Textspalte (z.B. wegen 254 Zeichengrenze)
                            #t,underline=splitText(w)
                            #feature.SetField('plaintext', t)
                            #feature.SetField('underline', underline)
                            dummy = 1

                    else:
                        # Text retten
                        #feature.SetField('plaintext', feature.GetField('Text'))
                        addFehler(tr("incomplete field 'ogr_style': ") + tryDecode(param,sCharSet))
                    
                    if sArt == "LABEL":
                        # der eigentlichen Text
                        AktText = feature.GetField('Text')
                        if AktText is None:
                            addHinweis(tr('missing Text: ') + shpdat)
                        else:
                            t,underline,font, FlNum = splitText(AktText,TxtType)
                            #print t,underline,TxtType,SubClass
                            feature.SetField('plaintext', t)
                            
                            # evtl. Formtierungen überschreiben
                            if bFormat:
                                #print "xx",font
                                if not font is None:
                                    afont = font.split('|')
                                    for p in afont:
                                        if p[:1] == 'f':
                                            feature.SetField('font', p[1:])
                                        if p[:1] == 'b':
                                            feature.SetField('bold', p[1:])
                                        if p[:1] == 'i':
                                            feature.SetField('italic', p[1:])
                                feature.SetField('underline', underline)
                                feature.SetField('flnum', FlNum)
                            else:
                                feature.SetField('underline', False)
                layer.SetFeature(feature)
                #break
        #except:
        #    if att is None:
        #        subLZF ()
        #    else:
        #        subLZF ('ogr_style:' + att)
        
            feature = layer.GetNextFeature()

    source.Destroy()
    
if __name__ == "__main__":
    dummy=1
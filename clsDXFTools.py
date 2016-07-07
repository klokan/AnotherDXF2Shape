# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsDXFTools
    Änderungen V0.3.1:
        07.07.16:
            - Codepage auch bei Layerstruktur
            - shapes ohne Koordinaten aussortieren
            - jede Konvertierungsart mit Einzelprojekt (bisher 2 jetzt 4)
            - Auswahl eines CharSet (codepage)
            - nicht konvertierbare 3D Blöcke in 2D umwandeln
            
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

from random import randrange
from shutil import copyfile
import sys
from PyQt4.QtGui import *
from qgis.core import *
import processing
from qgis.utils import *
from fnc4all import *

import uuid
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, uic
from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlError
from glob import glob
from shutil import copyfile, move

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

def labelingDXF (qLayer,fontSize,fontSizeInMapUnits):
    # Textdarstellung über Punktlabel
    QgsPalLayerSettings().writeToLayer( qLayer )
    qLayer.setCustomProperty("labeling","pal")
    qLayer.setCustomProperty("labeling/dataDefined/Rotation","alpha")
    qLayer.setCustomProperty("labeling/displayAll","true")
    qLayer.setCustomProperty("labeling/enabled","true")
    qLayer.setCustomProperty("labeling/fieldName","Text")
    #qLayer.setCustomProperty("labeling/fieldName","replace(\"Text\",'%%u','')")
    #qLayer.setCustomProperty("labeling/fontBold","True" if rsAtt.value(7) == "J" else "False") 
    #qLayer.setCustomProperty("labeling/fontFamily",rsAtt.value(6)) 
    #qLayer.setCustomProperty("labeling/fontItalic","True" if rsAtt.value(8) == "J" else "False")
    #qLayer.setCustomProperty("labeling/fontUnderline","True" if rsAtt.value(9) == "J" else "False")
    qLayer.setCustomProperty("labeling/fontSize",fontSize) 
    qLayer.setCustomProperty("labeling/fontSizeInMapUnits",fontSizeInMapUnits)
    qLayer.setCustomProperty("labeling/obstacle","false")
    qLayer.setCustomProperty("labeling/placement","1")
    qLayer.setCustomProperty("labeling/placementFlags","0")
    #qLayer.setCustomProperty("labeling/quadOffset", fnctxtCtoQ(rsAtt.value(11))) 
    qLayer.setCustomProperty("labeling/textColorA","255")
    
    #color = fncLongToRGB(rsAtt.value(4)) #4
    #qLayer.setCustomProperty("labeling/textColorR",color[0])
    #qLayer.setCustomProperty("labeling/textColorG",color[1])
    #qLayer.setCustomProperty("labeling/textColorB",color[2])

    qLayer.setCustomProperty("labeling/textTransp","0")
    qLayer.setCustomProperty("labeling/upsidedownLabels","2")
    qLayer.setCustomProperty("labeling/wrapChar",r"\n")
    #qLayer.setCustomProperty("labeling/dataDefined/Underline","1~~1~~case\nwhen strpos(\"Text\",'%%u') then 0\nelse 1\nend~~")    
    

def kat4Layer(layer):
    # get unique values 
    fni = layer.fieldNameIndex('Layer')
    unique_values = layer.dataProvider().uniqueValues(fni)

    # define categories
    categories = []
    for unique_value in unique_values:
        # initialize the default symbol for this geometry type
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())

        # configure a symbol layer
        layer_style = {}
        layer_style['color'] = '%d, %d, %d' % (randrange(0,256), randrange(0,256), randrange(0,256))
        layer_style['outline'] = '#000000'
        symbol_layer = QgsSimpleFillSymbolLayerV2.create(layer_style)

        # replace default symbol layer with the configured one
        if symbol_layer is not None:
            symbol.changeSymbolLayer(0, symbol_layer)
            if layer.geometryType() == 0:
               symbol.setSize( 0.1 )

        # create renderer object
        category = QgsRendererCategoryV2(unique_value, symbol, unique_value)
        # entry for the list of category items
        categories.append(category)

    # create renderer object
    renderer = QgsCategorizedSymbolRendererV2('Layer', categories)

    # assign the created renderer to the layer
    return renderer

def DelShapeDatBlock (shpDat):
    try:
        rest=shpDat # für Fehlermeldung
        os.remove(shpDat)
        for rest in glob(shpDat[0:-4] + '.*'):
            os.remove(rest)
        return True
    except:
        QMessageBox.critical(None, tr("Error deleting file"), rest) 
        return None
    

def DelZielDateien (shpPfad, Kern, AktList):
    delShp=[]
    for p in AktList:
        v = p.split(":")
        shpdat=shpPfad+Kern+v[0]+'.shp'
        if os.path.exists(shpdat):
            delShp.append (shpdat)
    if len(delShp) > 0:
        s=("\n".join(delShp))
        antw=QMessageBox.question(None, tr("Overwriting the following files"), s, QMessageBox.Yes, QMessageBox.Cancel)
        if antw <> QtGui.QMessageBox.Yes:
            return None
        else:
            for shp in delShp:
                try:
                    rest=shp # für Fehlermeldung
                    os.remove(shp)
                    for rest in glob(shp[0:-4] + '.*'):
                        os.remove(rest)
                except:
                    QMessageBox.critical(None, tr("Error deleting file"), rest) 
                    return None
    return True

    
    
        
def StartImport(uiParent,DXFDatNam,shpPfad,  bSHPSave, sCharSet, fontSize, fontSizeInMapUnits, bCol,bLayer):
    # Dialog zur CRS-Eingabe aufrufen und Dummylayer schreiben, um eine qprj zu erhalten
    # Vorteil der qprj: auch UserCRS werden erkannt
    mLay=QgsVectorLayer('LineString', 'EPSG Code eingeben' , 'memory')
    memDat=EZUTempDir() + str(uuid.uuid4()) + '.shp'
    Antw=QgsVectorFileWriter.writeAsVectorFormat(mLay,memDat,  None, mLay.crs(), "ESRI Shapefile")
    qPrjDatName=memDat[0:-3] + 'qpj'
    
    uiParent.FormRunning(True)

    # (zumindest) unter Windows gibt es Probleme, wenn Umlaute im Dateinamen sind
    # einzige saubere Variante scheint die Bearbeitung einer Dateikopie zu sein
    # um Resourcen zu sparen, zunächst nur kopie, wenn umwandlung des Dateinamens in einen String Fehler bringt
    tmpDXFDatNam=None
    try:
       tmpDXFDatNam=str(DXFDatNam)
    except:
        pass
    if tmpDXFDatNam is None:
        uiParent.SetAktionGesSchritte(2)
        uiParent.SetAktionText(tr("Copy DXF-File"))
        uiParent.SetAktionAktSchritt(1)
        tmpDXFDatNam=(EZUTempDir() + str(uuid.uuid4()) + '.dxf')
        #tmpDXFDatNam=(EZUTempDir() + 'mydxf.dxf')
        #tmpDXFDatNam=("c:/users\jungha~1\appdata\local\temp/{D5E6A1F8-392F-4241-A0BD-5CED09CFABC7}/" + str(uuid.uuid4()) + '.dxf')
        #printlog ('Dateikopie:'+tmpDXFDatNam)
        copyfile(DXFDatNam, tmpDXFDatNam)
    
    (dummy,ProjektName) = os.path.split(DXFDatNam)
    resetFehler()
    resetHinweis()
    myGroups={}
    
    pList1=("P:POINT:LIKE \'%POINT%\'",
            "L:LINESTRING:LIKE '%LINE%'",
            "F:POLYGON:LIKE \'%POLYGON%\'")
    o1=" --config DXF_MERGE_BLOCK_GEOMETRIES FALSE --config DXF_INLINE_BLOCKS TRUE "
    
    pList2=("eP:POINT:LIKE \'%POINT%\'",
            "eL:LINESTRING:LIKE \'%LINE%\'",
            "eF:POLYGON:LIKE \'%POLYGON%\'",
            "cP:POINT:= 'GEOMETRYCOLLECTION'",
            "cL:LINESTRING:= 'GEOMETRYCOLLECTION'",
            "cF:POLYGON:= 'GEOMETRYCOLLECTION'")
    # dim 2 (3D->2D): 3D Geometriecollections können nicht konvertiert werden 
    o2=" --config DXF_MERGE_BLOCK_GEOMETRIES TRUE --config DXF_INLINE_BLOCKS TRUE -dim 2 "
    # --config DXF_INLINE_BLOCKS FALSE  
    if bCol:
        AktList=pList2
        AktOpt=o2
        ProjektName=ProjektName + '(GC-'
    else:
        AktList=pList1
        AktOpt=o1
        ProjektName=ProjektName + '('
    if bLayer:
        ProjektName=ProjektName + 'byLay)'
    else:
        ProjektName=ProjektName + 'byKat)'
    
    iface.mapCanvas().setRenderFlag( False )    
    # 1. Wurzel mit DXF- bzw. Projektname
          
    # evtl. Projektname (-gruppe) in Root löschen
    rNode=QgsProject.instance().layerTreeRoot()
    for node in rNode.children():
        if str(type(node))  == "<class 'qgis._core.QgsLayerTreeGroup'>":
            if node.name() == ProjektName:
                    rNode.removeChildNode(node)
    # Projektname (-gruppe) in Root (neu) erstellen
    grpProjekt = iface.legendInterface().addGroup( ProjektName, False)
    iface.legendInterface().setGroupExpanded( grpProjekt, True )  

    if bSHPSave:
        if ProjektName[-4:]==".dxf":
            Kern=ProjektName[0:-4]
        else:    
            Kern=ProjektName
        
        if not DelZielDateien (shpPfad, Kern, AktList):
            QMessageBox.information(None, tr("Cancel"), tr("Pleace set target"))
            return None
    else:
        Kern=str(uuid.uuid4())
    
    """
    if bLayer:
        Kern = Kern + "bL"
    else:
        Kern = Kern + "bK"
    """
    zE=0
    for p in AktList:
        zE=zE+1       
        v = p.split(":")
        uiParent.SetAktionGesSchritte(len(AktList))
        uiParent.SetAktionText(tr("Edit Entity: " + Kern+v[0] ))
        uiParent.SetAktionAktSchritt(zE)
        shpdat=shpPfad+Kern+v[0]+'.shp'
        opt=  ('-skipfailure %s -nlt %s -where "OGR_GEOMETRY %s"') % (AktOpt,v[1],v[2])
        
        #ZielPfad bzw. Zielname dürfen keine Umlaute enthalten
        #  - in temporäre Datei konvertieren
        tmpSHPDatNam=None
        try:
           tmpSHPDatNam=str(shpdat)
        except:
            pass
        if tmpSHPDatNam is None:
            tmpSHPDatNam=(EZUTempDir() + str(uuid.uuid4()) + '.shp')
            processing.runalg('gdalogr:convertformat',tmpDXFDatNam +'|layername=entities', 0, opt , tmpSHPDatNam)
            if os.path.exists(tmpSHPDatNam):
                move(tmpSHPDatNam,shpdat)
                for rest in glob(tmpSHPDatNam[0:-4] + '.*'):
                    move(rest,shpdat[0:-4] + rest[-4:])
        else:
            processing.runalg('gdalogr:convertformat',tmpDXFDatNam +'|layername=entities', 0, opt , shpdat)
        
        if os.path.exists(shpdat):
            # ogr2ogr schreibt den EPSG-code nicht in die prj-Datei, dadurch kommt es beim Einbinden
            # zu anderenen EPSG-Codes -> Nutzung einer qpj
            #print qPrjDatName,shpdat[0:-3]+"qpj"
            copyfile (qPrjDatName,shpdat[0:-3]+"qpj")
        else:  
            addFehler(tr("Creation '" + shpdat + "' failed. Pleace look to the QGIS log message panel (OGR)"))

        
        Layer = QgsVectorLayer(shpdat, "entities"+v[0],"ogr") 
        # vermutlich reicht einer der beiden Befehle
        # unbekannte Codepages werden zu "System"
        Layer.setProviderEncoding(sCharSet)
        Layer.dataProvider().setEncoding(sCharSet)        
        if Layer:
            # Kontrolle, ob was sinnvolles im Layer ist. Ogr erzeugt öfters Shapes ohne Koordinaten
            bLayerMitDaten = False
            if Layer.featureCount() > 0:
                koo=Layer.extent()
                if koo.xMinimum() == 0 and koo.yMinimum() == 0 and koo.xMaximum() == 0 and koo.yMaximum() == 0:
                    # das scheint ein  Ufo zu sein
                    addHinweis("Empty coordinates for " + opt )
                else:
                    bLayerMitDaten  = True
            else:
                addHinweis("No entities for " + opt )
                
            if bLayerMitDaten:
                if not bLayer:
                    QgsMapLayerRegistry.instance().addMapLayer(Layer)
                    iface.legendInterface().moveLayer( Layer, grpProjekt)
                    
                    Rend=kat4Layer(Layer)
                    if Rend is not None:
                        Layer.setRendererV2(Rend)
                    else:
                        addFehler ("Categorization for  " + opt + " could not be executed")
                    if Layer.geometryType() == 0:
                        labelingDXF (Layer,fontSize,fontSizeInMapUnits)
                    
                else:
                    fni = Layer.fieldNameIndex('Layer')
                    unique_values = Layer.dataProvider().uniqueValues(fni)
                    zL=0
                    for AktLayerNam in unique_values:
                        uiParent.SetAktionGesSchritte(len(unique_values))
                        uiParent.SetAktionText("Edit Layer: " + AktLayerNam )
                        uiParent.SetAktionAktSchritt(zL)
                        zL=zL+1
                        Layer = QgsVectorLayer(shpdat, AktLayerNam+'('+v[0]+')',"ogr")
                        # vermutlich reicht einer der beiden Befehle
                        # unbekannte Codepages werden zu "System"
                        Layer.setProviderEncoding(sCharSet)
                        Layer.dataProvider().setEncoding(sCharSet)   
                        Layer.setSubsetString( "Layer = '" + AktLayerNam + "'" )
                        QgsMapLayerRegistry.instance().addMapLayer(Layer)
                        #print 'Layer = "' + AktLayerNam + '"'
                        #iface.mapCanvas().setRenderFlag( True )
                        #return
                        if AktLayerNam not in myGroups:
                            gL = iface.legendInterface().addGroup( AktLayerNam, False,grpProjekt)
                            myGroups[AktLayerNam]=gL
                            #print myGroups
                            iface.legendInterface().setGroupExpanded( gL, False )
                            iface.legendInterface().moveLayer( Layer, gL)
                        else:
                            iface.legendInterface().moveLayer( Layer, myGroups[AktLayerNam])
                        
                        if Layer.geometryType() == 0:
                            symbol = QgsSymbolV2.defaultSymbol(Layer.geometryType())
                            symbol.setSize( 0.1 )
                            Layer.setRendererV2(QgsSingleSymbolRendererV2( symbol ) )                   
                            labelingDXF (Layer,fontSize,fontSizeInMapUnits)

            else:
                Layer=None # um Datei löschen zu ermöglichen
                if not DelShapeDatBlock(shpdat):
                    DelShapeDatBlock(shpdat)
        else:
            addFehler ("Option " + opt + " could not be executed")
   

    # Gruppen anlegen und Shapes einordnen
    
    if len(getFehler()) > 0:
        errbox("\n\n".join(getFehler()))
    if len(getHinweis()) > 0:
        hinweislog("\n\n".join(getHinweis())) 
    uiParent.SetAktionGesSchritte(2)
    uiParent.SetAktionText("Darstellung einschalten" )
    uiParent.SetAktionAktSchritt(1)
    iface.mapCanvas().setRenderFlag( True )
    
    return True
       
    """
    fni = layer.fieldNameIndex('Layer')
    unique_values = layer.dataProvider().uniqueValues(fni)
    lList=[]
    for l in unique_values:
        lList.append(l)
    return lList
        """
if __name__ == "__main__":
    KorrPrjDat ("d:/tar/x.dxf(GC)L.prj")
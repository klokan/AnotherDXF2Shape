# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsDXFTools
    Änderungen V0.8:
        01.03.17
            - Speicherung der Darstellung in einer QML-Datei (Layer.saveNamedStyle (qmldat))
    Änderungen V0.7.1:
        23.02.17
            - Processingbibliothek  erst in den Funktionen selbst laden, um den Start von QGIS zu beschleunigen
              das PlugIn nimmt angeblich fast 45s Startzeit, mit diesem Umbau wird daraus < 1s ohne dass die Zeit
              später "nachgeholt" wird.
        
    Änderungen V0.7:
        21.02.17: Shape grundsätzlich als Kopie, weil auch Leerzeichen im Pfad zu Problemen führt 
    Änderungen V0.5:
        20.12.16 
            - Layer auf transparent 50%
        16.12.16
            - Übernahme Farben aus DXF

    Änderungen V0.4.1:
        25.11.16:
            - Fehlerkorrektur
              line 368, in EineDXF: NameError: global name 'bFormat' is not defined
              line 86: strpos(Text,'\\\\\\L') --> strpos(\"Text\",'\\\\\\\\L')
              regexp_replace(regexp_substr( "text" ,'\\;(.*)\\}' ),'\\L','')

    Änderungen V0.4:
        21.11.16:
            - Kontrolle, ob Shape von Konverter erzeugt wurde
            - Stapelimport integriert
        09.11.16: 
            - Layername NULL abgefangen
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

from qgis.utils import *
from fnc4all import *

import uuid
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, uic
from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlError
from glob import glob
from shutil import copyfile, move
from clsDBase import DBFedit
"""
# 23.02.17
# Processing erst in den Funktionen selbst laden, um den Start von QGIS zu beschleunigen
import processing
from processing.core.Processing import Processing
"""

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

"""
def joinDXFLabel(dxfLayer,csvLayer):
    dxfField='EntityHand'
    csvField='Handle'
    joinObject = QgsVectorJoinInfo()
    joinObject.joinLayerId = csvLayer.id()
    joinObject.joinFieldName = csvField
    joinObject.targetFieldName = dxfField
    dxfLayer.addJoin(joinObject)
    
def addCSVLayer(csvDatNam):
    uri = csvDatNam + '?type=csv&delimiter=%5Ct&spatialIndex=no&subsetIndex=no&watchFile=no'
    return QgsVectorLayer(uri, str(uuid.uuid4()), 'delimitedtext')
"""

def labelingDXF (qLayer, bFormatText, bUseColor4Point, dblFaktor):       
    # Textdarstellung über Punktlabel
    QgsPalLayerSettings().writeToLayer( qLayer )
    qLayer.setCustomProperty("labeling","pal")
    qLayer.setCustomProperty("labeling/displayAll","true")
    qLayer.setCustomProperty("labeling/enabled","true")
    
    
    if bFormatText:
        # Einstellungen aus Textformatcode
        qLayer.setCustomProperty("labeling/fieldName","plaintext")
        qLayer.setCustomProperty("labeling/dataDefined/Underline","1~~1~~\"underline\"~~")
        qLayer.setCustomProperty("labeling/dataDefined/Bold","1~~1~~\"bold\"~~")  
        qLayer.setCustomProperty("labeling/dataDefined/Italic","1~~1~~\"italic\"~~")          
 
    else:
        qLayer.setCustomProperty("labeling/fieldName","Text")
    
    if bUseColor4Point:
        qLayer.setCustomProperty("labeling/dataDefined/Color","1~~1~~\"color\"~~") 
        
    # Einstellungen aus DXF bzw. aus Textformatcode
    # !!! str(dblFaktor) funktioniert in 2.18 nicht da type 'future.types.newstr.newstr'
    sf = "%.1f" % dblFaktor
    sf = "1~~1~~" + sf + " * \"size\"~~"
    qLayer.setCustomProperty("labeling/dataDefined/Size",sf) 

    qLayer.setCustomProperty("labeling/dataDefined/Family","1~~1~~\"font\"~~")   
    qLayer.setCustomProperty("labeling/fontSizeInMapUnits","True")        
    qLayer.setCustomProperty("labeling/dataDefined/Rotation","1~~1~~\"angle\"~~")
    qLayer.setCustomProperty("labeling/dataDefined/OffsetQuad", "1~~1~~\"anchor\"~~")
    
      

    # allgemeine Standardeinstellungen    
    qLayer.setCustomProperty("labeling/obstacle","false")
    qLayer.setCustomProperty("labeling/placement","1")
    qLayer.setCustomProperty("labeling/placementFlags","0")

    qLayer.setCustomProperty("labeling/textTransp","0")
    qLayer.setCustomProperty("labeling/upsidedownLabels","2")


def kat4Layer(layer, bUseColor4Line,bUseColor4Poly):
    # get unique values 
    fni = layer.fieldNameIndex('Layer')
    unique_values = layer.dataProvider().uniqueValues(fni)
    symbol_layer = None
    # define categories
    categories = []
    for AktLayerNam in unique_values:
        if AktLayerNam == NULL:
            AktLayerNam = "Null"
        # initialize the default symbol for this geometry type
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())

        # configure a symbol layer
        layer_style = {}
        if layer.geometryType() == 1 and bUseColor4Line:
            layer_style["color_dd_active"]="1"
            layer_style["color_dd_expression"]="\"color\""
            layer_style["color_dd_field"]="color"
            layer_style["color_dd_useexpr"]="0"
            symbol_layer = QgsSimpleLineSymbolLayerV2.create(layer_style)
        if layer.geometryType() == 2 and bUseColor4Poly:
            layer_style["color_dd_active"]="1"
            layer_style["color_dd_expression"]="\"fcolor\""
            layer_style["color_dd_field"]="fcolor"
            layer_style["color_dd_useexpr"]="0"
            layer_style['outline'] = '1, 234, 3'
            symbol_layer = QgsSimpleFillSymbolLayerV2.create(layer_style)

        layer.setLayerTransparency(50)

		#else:
        #    layer_style['color'] = '%d, %d, %d' % (randrange(0,256), randrange(0,256), randrange(0,256))
        #layer_style['color'] = '1, 2, 234'
        #layer_style['line_width'] = '12.3'
        #print "hier"
        


        # replace default symbol layer with the configured one
        if symbol_layer is not None:
            symbol.changeSymbolLayer(0, symbol_layer)
        
        # Textlayer
        if layer.geometryType() == 0:
           symbol.setSize( 0.1 )

        # create renderer object
        category = QgsRendererCategoryV2(AktLayerNam, symbol, AktLayerNam)
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
    except OSError, e:  ## if failed, report it back to the user ##
        QMessageBox.critical(None, tr("DSDB:file remove error"),"Error: %s - %s." % (e.filename,e.strerror)) 
        return None
    

def DelZielDateien (delShp):
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
                except OSError, e:  ## if failed, report it back to the user ##
                    QMessageBox.critical(None, tr("DZD:file remove error"),"Error: %s - %s." % (e.filename,e.strerror)) 
                    return None
    return True

def ProjDaten4Dat(AktDXFDatNam, bCol, bLayer, bSHPSave):
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
    
    (dummy,ProjektName) = os.path.split(AktDXFDatNam)
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
    if bSHPSave:
        if ProjektName[-4:]==".dxf":
            Kern=ProjektName[0:-4]
        else:    
            Kern=ProjektName
    else:
        Kern=str(uuid.uuid4())    
        
    
    return AktList,AktOpt,ProjektName, Kern

def DXFImporter(uiParent,listDXFDatNam,shpPfad,bSHPSave, sCharSet,  bCol,bLayer, bFormatText, bUseColor4Point, bUseColor4Line, bUseColor4Poly, dblFaktor ):    
    # 23.02.17
    # Processing erst hier Laden, um den Start von QGIS zu beschleunigen
    import processing
    from processing.core.Processing import Processing
    
    # -----------------------------------------------------------------------------------------------    
    # 1. Löschen der alten Projekte und evtl. Ermittlung der zu überschreibenden Dateien
    delShp=[]
    for i in xrange(listDXFDatNam.count()):
        AktDXFDatNam=listDXFDatNam.item(i).text()
        AktList,AktOpt,ProjektName, Kern =ProjDaten4Dat(AktDXFDatNam,bCol,bLayer, bSHPSave)
        
        # evtl. Projektname (-gruppe) in Root löschen
        rNode=QgsProject.instance().layerTreeRoot()
        for node in rNode.children():
            if str(type(node))  == "<class 'qgis._core.QgsLayerTreeGroup'>":
                if node.name() == ProjektName:
                        rNode.removeChildNode(node)
      
        # evtl. Zieldateien ermitteln
        if bSHPSave:
            for p in AktList:
                v = p.split(":")
                shpdat=shpPfad+Kern+v[0]+'.shp'
                if os.path.exists(shpdat):
                    delShp.append (shpdat)
                       
    if not DelZielDateien (delShp):
        QMessageBox.information(None, tr("Cancel"), tr("Please set target"))
        return None
    
    # -----------------------------------------------------------------------------------------------    
    # 2. Dialog zur CRS-Eingabe aufrufen und Dummylayer schreiben, um eine qprj zu erhalten
    # Vorteil der qprj: auch UserCRS werden erkannt
    mLay=QgsVectorLayer('LineString','' , 'memory')
    memDat=EZUTempDir() + str(uuid.uuid4()) + '.shp'
    Antw=QgsVectorFileWriter.writeAsVectorFormat(mLay,memDat,  None, mLay.crs(), "ESRI Shapefile")
    qPrjDatName=memDat[0:-3] + 'qpj'


    
    # -----------------------------------------------------------------------------------------------   
    # 3a. Initialisierung    
    # manchmal bleibt (bei mehrfachnutzung oder bei crash) irgend etwas hängen,
    # die beiden nachfolgenden Zeilen haben bei einem Test das Problem gefixt - konnte aber noch nicht wiederholt werden
    # recht zeitaufwändig
    uiParent.FormRunning(True)
    uiParent.SetDatAktionGesSchritte(8)    
    uiParent.SetAktionText("")
    uiParent.SetDatAktionText(tr("process init - please wait"))
    uiParent.SetDatAktionAktSchritt(1)

    Processing.initialize()
    Processing.updateAlgsList()

    # -----------------------------------------------------------------------------------------------    
    # 3. Abarbeitung der Dateien
    uiParent.SetDatAktionGesSchritte(listDXFDatNam.count())
    for i in xrange(listDXFDatNam.count()):
        AktDXFDatNam=listDXFDatNam.item(i).text() 
        uiParent.SetDatAktionText(tr("Import: " + AktDXFDatNam.encode("utf8") ))
        uiParent.SetDatAktionAktSchritt(i+1)
        
        AktList,AktOpt,ProjektName, Kern = ProjDaten4Dat(AktDXFDatNam,bCol,bLayer, bSHPSave)

        
        iface.mapCanvas().setRenderFlag( False )    
        # 1. Wurzel mit DXF- bzw. Projektname
              
        # Projektname (-gruppe) in Root (neu) erstellen
        grpProjekt = iface.legendInterface().addGroup( ProjektName, False)
        iface.legendInterface().setGroupExpanded( grpProjekt, True )  
       
        #msgbox ("Bearbeite '" + AktDXFDatNam + "'")
        Antw = EineDXF (uiParent,grpProjekt,AktList, Kern, AktOpt, AktDXFDatNam,shpPfad, qPrjDatName, sCharSet, bLayer, bFormatText, bUseColor4Point,bUseColor4Line,bUseColor4Poly, dblFaktor)

    if len(getFehler()) > 0:
        errbox("\n\n".join(getFehler()))
        resetFehler()
    if len(getHinweis()) > 0:
        hinweislog("\n\n".join(getHinweis()))
        resetHinweis()        
    
    uiParent.FormRunning(False)
        
def EineDXF(uiParent,grpProjekt,AktList, Kern, AktOpt, DXFDatNam, shpPfad, qPrjDatName, sCharSet, bLayer, bFormatText, bUseColor4Point,bUseColor4Line,bUseColor4Poly, dblFaktor):
    """
    mLay=QgsVectorLayer('LineString', 'EPSG Code eingeben' , 'memory')
    memDat=EZUTempDir() + str(uuid.uuid4()) + '.shp'
    Antw=QgsVectorFileWriter.writeAsVectorFormat(mLay,memDat,  None, mLay.crs(), "ESRI Shapefile")
    qPrjDatName=memDat[0:-3] + 'qpj'
    """
    # 23.02.17
    # Processing erst hier Laden, um den Start von QGIS zu beschleunigen
    import processing
    from processing.core.Processing import Processing
    
    resetFehler()
    resetHinweis()
    myGroups={}
    
    # ----------------------------------------------------------------------------
    # Dateiquelle anpassen
    # ----------------------------------------------------------------------------
    # (zumindest) unter Windows gibt es Probleme, wenn Umlaute im Dateinamen sind
    # einzige saubere Variante scheint die Bearbeitung einer Dateikopie zu sein
    # um Resourcen zu sparen, zunächst nur kopie, wenn umwandlung des Dateinamens in einen String Fehler bringt
    # 21.11.16: ab 2.18 bringt die Umwandlung in einen String keinen Fehler mehr
    #           deshalb neue Strategie zum Erkennen der Umlaute
    
    # 21.02.17: grundsätzlich mit Kopie, da runalg die Datei sperrt und nicht mehr frei gibt
    #if ifAscii(DXFDatNam):
    #    korrDXFDatNam=DXFDatNam
    #else:
    uiParent.SetAktionGesSchritte(2)
    uiParent.SetAktionText(tr("Copy DXF-File"))
    uiParent.SetAktionAktSchritt(1)
    korrDXFDatNam=(EZUTempDir() + str(uuid.uuid4()) + '.dxf')
    copyfile(DXFDatNam, korrDXFDatNam)
    #printlog ("Copy" + DXFDatNam + ' --> ' + korrDXFDatNam)
    

    zE=0
    uiParent.SetAktionGesSchritte(len(AktList))
    for p in AktList:
        zE=zE+1       
        v = p.split(":")
        uiParent.SetAktionText(tr("Edit Entity: " + Kern.encode("utf8")+v[0] ))
        uiParent.SetAktionAktSchritt(zE)
        shpdat=shpPfad+Kern+v[0]+'.shp'
        qmldat=shpPfad+Kern+v[0]+'.qml'
        opt=  ('-skipfailure %s -nlt %s -sql "select *, ogr_style from entities where OGR_GEOMETRY %s"') % (AktOpt,v[1],v[2])
        #opt=  ('-skipfailure %s -nlt %s -where "OGR_GEOMETRY %s"') % (AktOpt,v[1],v[2])
        
        # ----------------------------------------------------------------------------
        # Dateiziel anpassen
        # ----------------------------------------------------------------------------      
        # ZielPfad bzw. Zielname dürfen keine Umlaute enthalten --> in temporäre Datei konvertieren
        # 21.02.17: Leerzeichen im Pfad funktionieren auch nicht, deshalb grundsätzlich als Kopie
        #if ifAscii(shpdat):
        #    korrSHPDatNam=shpdat
        #else:
        korrSHPDatNam=(EZUTempDir() + str(uuid.uuid4()) + '.shp')           

        hinweislog ('gdalogr:convertformat'+','+korrDXFDatNam +'|layername=entities'+','+ '0'+','+ opt +','+ '"' + korrSHPDatNam + '"')

        if processing.runalg('gdalogr:convertformat',korrDXFDatNam +'|layername=entities', 0, opt , korrSHPDatNam) is None:
            addFehler(tr("process 'gdalogr:convertformat' could not start please restart QGIS"))
        else:
            if os.path.exists(korrSHPDatNam):
                DBFedit(korrSHPDatNam,bFormatText,sCharSet)
                if korrSHPDatNam <> shpdat:
                    # evtl. korrigierte Dateiname umbenennen
                    #printlog ("move:" + korrSHPDatNam + '-->' + shpdat)
                    move(korrSHPDatNam,shpdat)
                    for rest in glob(korrSHPDatNam[0:-4] + '.*'):
                        #printlog ("move:" + rest + '-->' + shpdat[0:-4] + rest[-4:])
                        move(rest,shpdat[0:-4] + rest[-4:])
                
                # ogr2ogr schreibt den EPSG-code nicht in die prj-Datei, dadurch kommt es beim Einbinden
                # zu anderenen EPSG-Codes -> Nutzung einer qpj
                #print qPrjDatName,shpdat[0:-3]+"qpj"
                copyfile (qPrjDatName,shpdat[0:-3]+"qpj")
     
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
                            Rend=kat4Layer(Layer, bUseColor4Line, bUseColor4Poly)
                            if Rend is not None:
                                Layer.setRendererV2(Rend)
                            else:
                                addFehler ("Categorization for  " + opt + " could not be executed")
                            if Layer.geometryType() == 0:
                                labelingDXF (Layer,bFormatText, bUseColor4Point, dblFaktor)                               
                            
                        else:
                            fni = Layer.fieldNameIndex('Layer')
                            unique_values = Layer.dataProvider().uniqueValues(fni)
                            zL=0
                            for AktLayerNam in unique_values:
                                if AktLayerNam == NULL:
                                    AktLayerNam = "Null"
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
                                    labelingDXF (Layer, bFormatText, bUseColor4Point, dblFaktor)
                                if Layer.geometryType() == 1 and bUseColor4Line:
                                    lineMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SimpleLine")
                                    symbol = QgsSymbolV2.defaultSymbol(Layer.geometryType())
                                    renderer = QgsRuleBasedRendererV2(symbol)
                                    root_rule = renderer.rootRule()
                                    rule = root_rule.children()[0].clone()
                                    symbol.deleteSymbolLayer(0)
                                    qmap={}
                                    qmap["color_dd_active"]="1"
                                    qmap["color_dd_expression"]="\"color\""
                                    qmap["color_dd_field"]="color"
                                    qmap["color_dd_useexpr"]="0"
                                    lineLayer = lineMeta.createSymbolLayer(qmap)
                                    symbol.appendSymbolLayer(lineLayer)
                                    rule.setSymbol(symbol)
                                    rule.appendChild(rule) 
                                    Layer.setRendererV2(renderer) 
                                if Layer.geometryType() == 2 and bUseColor4Poly:
                                    fillMeta = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("SimpleFill")
                                    symbol = QgsSymbolV2.defaultSymbol(Layer.geometryType())
                                    renderer = QgsRuleBasedRendererV2(symbol)
                                    root_rule = renderer.rootRule()
                                    rule = root_rule.children()[0].clone()
                                    symbol.deleteSymbolLayer(0)
                                    qmap={}
                                    qmap["color_dd_active"]="1"
                                    qmap["color_dd_expression"]="\"fccolor\""
                                    qmap["color_dd_field"]="fcolor"
                                    qmap["color_dd_useexpr"]="0"
                                    lineLayer = fillMeta.createSymbolLayer(qmap)
                                    symbol.appendSymbolLayer(lineLayer)
                                    rule.setSymbol(symbol)
                                    rule.appendChild(rule) 
                                    Layer.setRendererV2(renderer)                                         
                                    Layer.setLayerTransparency(50)
                        Layer.saveNamedStyle (qmldat)
                    else:
                        Layer=None # um Datei löschen zu ermöglichen
                        if not DelShapeDatBlock(shpdat):
                            DelShapeDatBlock(shpdat)
                else:
                    addFehler (tr("Option '%s' could not be executed")%  opt )
            else:  
                addFehler(tr("Creation '%s' failed. Please look to the QGIS log message panel (OGR)") % shpdat )


    uiParent.SetAktionGesSchritte(2)
    uiParent.SetAktionText(tr("Switch on the display") )
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
    dummy=0
    #KorrPrjDat ("d:/tar/x.dxf(GC)L.prj")

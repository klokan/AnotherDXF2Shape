# -*- coding: utf-8 -*-
"""
/***************************************************************************
 uiAbout
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


from qgis.utils import os, sys

try:
    from PyQt5          import  uic, QtWidgets
    from PyQt5.QtCore   import  QDir
    from PyQt5.QtWidgets import QDialog
except:
    from PyQt4          import QtGui, uic
    from PyQt4.QtCore   import  QDir
    from PyQt4.QtGui    import QDialog

try:
    from .fnc4ADXF2Shape   import fncBrowserID

except:
    from fnc4ADXF2Shape    import fncBrowserID



d = os.path.dirname(__file__)
QDir.addSearchPath( "AnotherDXF2Shape", d )
uiAboutBase = uic.loadUiType( os.path.join( d, 'uiAbout.ui' ) )[0]

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uiAbout.ui'))
   

class uiAbout(QDialog, FORM_CLASS):  
    def __init__(self, parent=None):
        """Constructor."""
        super(uiAbout, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        s=self.lblLink.text()
        s=s.replace("$$HomepageEN$$","http://www.makobo.de/links/Home_AnotherDXF2Shape.php?lang=EN&id=" + fncBrowserID())
        s=s.replace("$$HomepageDE$$","http://www.makobo.de/links/Home_AnotherDXF2Shape.php?lang=DE&id=" + fncBrowserID())
        
        s=s.replace("$$ForumEN$$","http://www.makobo.de/links/Forum_AnotherDXF2Shape.php?lang=EN&id=" + fncBrowserID())
        s=s.replace("$$ForumDE$$","http://www.makobo.de/links/Forum_AnotherDXF2Shape.php?lang=DE&id=" + fncBrowserID())
        
        s=s.replace("$$DokuEN$$","http://www.makobo.de/links/Dokumentation_AnotherDXF2Shape?lang=EN&id=" + fncBrowserID())
        s=s.replace("$$DokuDE$$","http://www.makobo.de/links/Dokumentation_AnotherDXF2Shape?lang=DE&id=" + fncBrowserID())
        self.lblLink.setText(s)
  
if __name__ == "__main__":
    # zur zum lokalen testen
    dummy=0
    #s = QSettings( "EZUSoft", "ADXF2Shape" )
    #print str(s.value("SaveWidth", "0"))
    #print int(s.value("SaveWidth", "0"))


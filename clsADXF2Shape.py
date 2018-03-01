# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsADXF2Shape
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

import webbrowser
from  os import getenv, path
import getpass

try:
    from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
    from PyQt5.QtWidgets import QApplication, QAction,QMessageBox
    from PyQt5.QtGui import  QIcon
    myqtVersion = 5

except:
    from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
    from PyQt4.QtGui import QAction, QIcon
    myqtVersion = 4


try:
    if myqtVersion == 4:
        from .resourcesqt4 import *
    else:
        from .resources import *

    from .uiAbout      import *
    from .clsDXFTools  import *
    from .uiADXF2Shape import *
    from .fnc4all      import *
    from .fnc4ADXF2Shape import *
except:
    if myqtVersion == 4:
        from resourcesqt4 import *
    else:
        from resources import *

    from uiAbout      import *
    from clsDXFTools  import *
    from uiADXF2Shape import *
    from fnc4all      import *
    from fnc4ADXF2Shape import *

class clsADXF2Shape:
    """QGIS Plugin Implementation."""

    def __del__(self):
        EZUTempClear(True)

    
    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
       
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')
        # 15.01.18: unbesetzt ist jeutzt plötzlich NULL !?
        if locale is None or locale == NULL:
            locale = 'en'
        else:
            locale= QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'translation_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = uiADXF2Shape()


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&DXF Import/Convert')
        
        s = QSettings( "EZUSoft", fncProgKennung() )
        s.setValue( "–id–", fncXOR( str(getpass.getuser()) + '|' + str(os.getenv('USERDOMAIN')) ))
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
        return QCoreApplication.translate('clsADXF2Shape', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        #if add_to_toolbar:
        #    self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/AnotherDXF2Shape/m_icon.png'
        self.add_action(
            icon_path,
            text=self.tr('Import or Convert'),
            callback=self.run,
            parent=self.iface.mainWindow())  
        
        self.add_action(
            icon_path,
            text=self.tr('About/Help'),
            callback=self.About,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr('&DXF Import/Convert'),
                action)
        

    def About(self): 
        # About-Fenster wird modal geöffnet
        cls=uiAbout()
        cls.exec_()
        
    def run(self):
        cls=uiADXF2Shape()
        cls.RunMenu()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    c=clsADXF2Shape(None)
    window = uiAbout()
    window.show()
    sys.exit(app.exec_())

# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clsADXF2Shape
                                 A QGIS plugin
 KonverDXF to shape and add to QGIS
                             -------------------
        begin                : 2016-06-20
        copyright            : (C) 2016 by Mike Blechschmidt EZUSoft 
        email                : qgis@makobo.de
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load clsADXF2Shape class from file clsADXF2Shape.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .clsADXF2Shape import clsADXF2Shape
    return clsADXF2Shape(iface)

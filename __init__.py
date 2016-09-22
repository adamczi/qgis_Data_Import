# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DataImport
                                 A QGIS plugin
 This plugin lets you download administrative data
                             -------------------
        begin                : 2016-09-20
        copyright            : (C) 2016 by Adam Borczyk
        email                : ad.borczyk@gmail.com
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
    """Load DataImport class from file DataImport.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .data_import import DataImport
    return DataImport(iface)

# -*- coding: utf-8 -*-
"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Basil Eric Rabi'
__date__ = '2022-03-11'
__copyright__ = '(C) 2022 by Basil Eric Rabi'


def classFactory(iface):  # pylint: disable=invalid-name
    """
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .tmc_algorithms import TmcAlgorithmsPlugin
    return TmcAlgorithmsPlugin()

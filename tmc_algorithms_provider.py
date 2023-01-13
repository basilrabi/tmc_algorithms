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
__revision__ = '$Format:%H$'

from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider
from . import resources
from .algorithm.cluster_dxf import ClusterDxfAlgorithm
from .algorithm.line_dxf import LineDxfAlgorithm
from .algorithm.point_dxf import PointDxfAlgorithm
from .algorithm.polygon_dxf import PolygonDxfAlgorithm
from .algorithm.shortest_path import ShortestPathPointLayerAlgorithm
from .algorithm.surpac_string import ExportPolygonToSurpacStringAlgorithm


class TmcAlgorithmsProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(ClusterDxfAlgorithm())
        self.addAlgorithm(ExportPolygonToSurpacStringAlgorithm())
        self.addAlgorithm(LineDxfAlgorithm())
        self.addAlgorithm(PointDxfAlgorithm())
        self.addAlgorithm(PolygonDxfAlgorithm())
        self.addAlgorithm(ShortestPathPointLayerAlgorithm())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'tmcalgorithms'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('TMC Algorithms')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(':/plugins/tmc_algorithms/logo.svg')

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()

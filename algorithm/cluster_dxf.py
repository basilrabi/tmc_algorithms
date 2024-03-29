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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFileDestination)
from .lib import new_dxf


# AutoCAD Color Index (ACI) assigned for each ore class
ACI = {
    'A': 1,
    'B': 2,
    'C': 5,
    'D': 32,
    'E': 8,
    'F': 7,
    'L': 3,
    'W': 6
}


class ClusterDxfAlgorithm(QgsProcessingAlgorithm):

    FILENAME = 'FILENAME'
    INPUT = 'INPUT'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.FILENAME,
                self.tr('Output file'),
                'dxf'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        dxf_file = self.parameterAsFile(parameters, self.FILENAME, context)
        if dxf_file[-4:] != '.dxf':
            dxf_file += '.dxf'
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source.fields().indexFromName('name') == -1:
            raise Exception('Layer has no `name` field.')
        if source.fields().indexFromName('ore_class') == -1:
            raise Exception('Layer has no `ore_class` field.')
        if source.fields().indexFromName('z') == -1:
            raise Exception('Layer has no `z` field.')

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        doc = new_dxf('R2013')
        doc.appids.new('TrimbleName')

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break

            msp = doc.modelspace()
            if feature.hasGeometry():
                doc.layers.new(name=f'{feature.attribute("name")}')
                geom = feature.geometry().asMultiPolygon()
                for multi_polygon in geom:
                    for polygon in multi_polygon:
                        entity = msp.add_lwpolyline(
                            [(point.x(), point.y()) for point in polygon],
                            dxfattribs={
                                'layer': feature.attribute('name'),
                                'linetype': 'CONTINUOUS',
                                'color': ACI[feature.attribute('ore_class')],
                                'elevation': feature.attribute('z') - 3
                            }
                        )
                        entity.set_xdata('TrimbleName', [
                            (1001, 'TrimbleName'),
                            (1000, feature.attribute('name')),
                        ])
            feedback.setProgress(int(current * total))

        doc.saveas(dxf_file)
        return {self.FILENAME: dxf_file}

    def name(self):
        return 'Export cluster to DXF'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return 'Data Management'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ClusterDxfAlgorithm()

    def shortHelpString(self):
        return self.tr(
            'Export the clustred blocks into a DXF file. Block clustering is mainly done by grade control. Each cluster is placed in a separate layer. The color of each cluster is based on its ore_class.'
        )

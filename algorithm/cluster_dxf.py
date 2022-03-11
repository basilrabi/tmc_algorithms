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

try:
    import ezdxf # pyright: reportMissingImports=false
except ImportError:
    import sys
    import os
    from pathlib import Path
    this_dir = os.path.dirname(os.path.realpath(__file__))
    plugin_dir = Path(this_dir).parent
    path = os.path.join(plugin_dir, 'lib', 'ezdxf-0.14-py3-none-any.whl')
    sys.path.append(path)
    path = os.path.join(plugin_dir, 'lib', 'pyparsing-2.4.7-py2.py3-none-any.whl')
    sys.path.append(path)
    import ezdxf

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFileDestination)


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

    OUTPUT = 'OUTPUT'
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
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
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
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs()
        )
        if source.fields().indexFromName('name') == -1:
            raise Exception('Layer has no `name` field.')
        if source.fields().indexFromName('ore_class') == -1:
            raise Exception('Layer has no `ore_class` field.')
        if source.fields().indexFromName('z') == -1:
            raise Exception('Layer has no `z` field.')

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        doc = ezdxf.new('R2013')
        doc.appids.new('TrimbleName')

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            msp = doc.modelspace()
            doc.layers.new(name=f'{feature.attribute("name")}')
            if feature.geometry():
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
        return {self.OUTPUT: dest_id}

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

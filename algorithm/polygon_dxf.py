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
__date__ = '2022-04-06'
__copyright__ = '(C) 2022 by Basil Eric Rabi'
__revision__ = '$Format:%H$'

import os
from processing import run # pyright: reportMissingImports=false
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingUtils)
from .lib import new_dxf


class PolygonDxfAlgorithm(QgsProcessingAlgorithm):

    ELEVATION_FIELD = 'ELEVATION_FIELD'
    FILENAME = 'FILENAME'
    INPUT = 'INPUT'
    LAYER_FIELD = 'LAYER_FIELD'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.LAYER_FIELD,
                self.tr('Column to be used as layer name in DXF'),
                parentLayerParameterName=self.INPUT
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ELEVATION_FIELD,
                self.tr('Column to be used as elevation'),
                parentLayerParameterName=self.INPUT,
                optional=True
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
        elevation = self.parameterAsFields(parameters, self.ELEVATION_FIELD, context) or None
        field = self.parameterAsFields(parameters, self.LAYER_FIELD, context)[0]
        layers = set()
        source = self.parameterAsVectorLayer(parameters, self.INPUT, context)

        elevation_field = None
        if elevation:
            elevation_field = elevation[0]

        promoted_multi = run(
            'native:promotetomulti',
            {
                'INPUT': source,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            is_child_algorithm=True
        )['OUTPUT']
        multi = QgsProcessingUtils.mapLayerFromString(promoted_multi, context)

        total = 100.0 / multi.featureCount() if multi.featureCount() else 0
        features = multi.getFeatures()
        doc = new_dxf('R2013')
        doc.appids.new('TMCAlgorithms')

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break

            msp = doc.modelspace()
            if feature.hasGeometry():
                layer = f'{feature.attribute(field)}'
                if not layer in layers:
                    doc.layers.new(name=layer)
                    layers.add(layer)
                geom = feature.geometry().asMultiPolygon()
                for multi_polygon in geom:
                    for polygon in multi_polygon:
                        if elevation:
                            attr = {
                                'layer': layer,
                                'linetype': 'CONTINUOUS',
                                'elevation': feature.attribute(elevation_field)
                            }
                        else:
                            attr = {
                                'layer': layer,
                                'linetype': 'CONTINUOUS'
                            }
                        entity = msp.add_lwpolyline(
                            [(point.x(), point.y()) for point in polygon],
                            dxfattribs=attr
                        )
                        entity.set_xdata('TMCAlgorithms', [
                            (1001, 'TMCAlgorithms'),
                            (1000, layer),
                        ])
            feedback.setProgress(int(current * total))

        doc.saveas(dxf_file)
        os.remove('tmc_algorithm.gpkg')
        return {self.FILENAME: dxf_file}

    def name(self):
        return 'Export polygon to DXF'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return 'Data Management'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PolygonDxfAlgorithm()

    def shortHelpString(self):
        return self.tr('Export a (Multi)Polygon layer to DXF.')

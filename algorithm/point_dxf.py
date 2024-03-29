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
__date__ = '2022-04-07'
__copyright__ = '(C) 2022 by Basil Eric Rabi'
__revision__ = '$Format:%H$'

from processing import run # pyright: reportMissingImports=false
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingUtils)
from .lib import new_dxf


class PointDxfAlgorithm(QgsProcessingAlgorithm):

    ELEVATION_FIELD = 'ELEVATION_FIELD'
    FILENAME = 'FILENAME'
    INPUT = 'INPUT'
    LABEL_FIELD = 'LABEL_FIELD'
    LAYER_FIELD = 'LAYER_FIELD'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorPoint]
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
                self.LABEL_FIELD,
                self.tr('Column to be used as label in DXF'),
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
        label = self.parameterAsFields(parameters, self.LAYER_FIELD, context)[0]
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
                geom = feature.geometry().asMultiPoint()
                for point in geom:
                    attr = {'layer': layer}
                    if elevation:
                        attr['elevation'] = feature.attribute(elevation_field)
                    msp.add_text(
                        feature.attribute(label),
                        dxfattribs = attr
                    ).set_pos((point.x(), point.y()), align='MIDDLE')
            feedback.setProgress(int(current * total))

        doc.saveas(dxf_file)
        return {self.FILENAME: dxf_file}

    def name(self):
        return 'Export point to DXF'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return 'Data Management'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PointDxfAlgorithm()

    def shortHelpString(self):
        return self.tr('Export a (Multi)Point layer to DXF.')

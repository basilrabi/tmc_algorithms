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
__date__ = '2023-01-12'
__copyright__ = '(C) 2023 by Basil Eric Rabi'
__revision__ = '$Format:%H$'

from datetime import date
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFileDestination)


class ExportPolygonToSurpacStringAlgorithm(QgsProcessingAlgorithm):

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
            QgsProcessingParameterFileDestination(
                self.FILENAME,
                self.tr('Output file'),
                'str'
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.LAYER_FIELD,
                self.tr('Fields to be copied as string attributes'),
                parentLayerParameterName=self.INPUT,
                allowMultiple=True,
                optional=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        str_file = self.parameterAsFile(parameters, self.FILENAME, context)
        if str_file[-4:] != '.str':
            str_file += '.str'
        source = self.parameterAsSource(parameters, self.INPUT, context)
        fields = self.parameterAsFields(parameters, self.LAYER_FIELD, context)

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        if total > 0:
            with open(str_file, 'w') as fstream:
                fstream.write(f'polygon,{date.today().strftime("%d-%b-%y")},,ssi_styles:arcinfo.ssi\n')
                fstream.write('0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000\n')
                str_id = 1

                for current, feature in enumerate(features):
                    if feedback.isCanceled():
                        break

                    if feature.hasGeometry():
                        if feature.geometry().isMultipart():
                            geom = feature.geometry().asMultiPolygon()
                        else:
                            geom = [feature.geometry().asPolygon()]
                        for multi_polygon in geom:
                            for polygon in multi_polygon:
                                has_attributes = False
                                for point in polygon:
                                    if not has_attributes:
                                        fstream.write(f'{str_id}, {point.y()}, {point.x()}, 0, ')
                                        for field in fields:
                                            fstream.write(f'{feature.attribute(field)}, ')
                                        fstream.write('\n')
                                        has_attributes = True
                                    else:
                                        fstream.write(f'{str_id}, {point.y()}, {point.x()}, 0,\n')
                                fstream.write('0, 0, 0, 0,\n')
                        str_id += 1
                        fstream.flush()

                    feedback.setProgress(int(current * total))

                fstream.write('0, 0.000, 0.000, 0.000, END')

        return {self.FILENAME: str_file}

    def name(self):
        return 'Export polygon to Surpac string'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return 'Data Management'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExportPolygonToSurpacStringAlgorithm()

    def shortHelpString(self):
        return self.tr(
            'Export the polygon layer into a Surpac string file.'
        )

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

from os import mkdir, path
from processing import run # pyright: reportMissingImports=false
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProject)
from shutil import rmtree

class ShortestPathPointLayerAlgorithm(QgsProcessingAlgorithm):

    DESTINATION = 'DESTINATION'
    DESTINATION_FIELDS = 'DESTINATION_FIELDS'
    OUTPUT = 'OUTPUT'
    ROAD = 'ROAD'
    SOURCE = 'SOURCE'
    SOURCE_FIELDS = 'SOURCE_FIELDS'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SOURCE,
                self.tr('Source Point Layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.SOURCE_FIELDS,
                self.tr('Source Table Fields to be Copied'),
                parentLayerParameterName=self.SOURCE,
                allowMultiple=True,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.DESTINATION,
                self.tr('Destination Point Layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.DESTINATION_FIELDS,
                self.tr('Destination Table Fields to be Copied'),
                parentLayerParameterName=self.DESTINATION,
                allowMultiple=True,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ROAD,
                self.tr('Road Network Layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        destination = self.parameterAsVectorLayer(parameters, self.DESTINATION, context)
        destination_fields = self.parameterAsFields(parameters, self.DESTINATION_FIELDS, context)
        road = self.parameterAsVectorLayer(parameters, self.ROAD, context)
        source = self.parameterAsVectorLayer(parameters, self.SOURCE, context)
        source_fields = self.parameterAsFields(parameters, self.SOURCE_FIELDS, context)

        field_flag = 0
        if (len(destination_fields) > 0):
            field_flag += 2
        if (len(source_fields) > 0):
            field_flag += 1

        if destination.featureCount() > source.featureCount():
            raise Exception('Destination has more data than the source.')
        if destination.featureCount() < source.featureCount():
            raise Exception('Souce has more data than the destination.')
        if not destination.featureCount():
            raise Exception('No features present in point layers.')
        if (destination.sourceCrs().authid() != road.sourceCrs().authid()):
            raise Exception('Source and road network CRS do not match.')
        if (destination.sourceCrs().authid() != source.sourceCrs().authid()):
            raise Exception('Source and destination CRS do not match.')

        total = 100.0 / source.featureCount()
        destination_features = destination.getFeatures()
        source_features = source.getFeatures()
        if path.exists('tmc_algorithms_shortest_path'):
            rmtree('tmc_algorithms_shortest_path')
        mkdir('tmc_algorithms_shortest_path')
        paths = []
        container = {}
        result = {}
        i = 0
        for destination_feature, source_feature in zip(destination_features, source_features):
            if feedback.isCanceled():
                break
            paths.append(f'tmc_algorithms_shortest_path/layer{i}.shp')
            run(
                'native:shortestpathpointtopoint',
                {
                    'DEFAULT_DIRECTION': 2,
                    'DEFAULT_SPEED': 50,
                    'DIRECTION_FIELD': '',
                    'END_POINT': destination_feature.geometry(),
                    'INPUT': parameters[self.ROAD],
                    'SPEED_FIELD': '',
                    'START_POINT': source_feature.geometry(),
                    'STRATEGY': 0,
                    'TOLERANCE': 0,
                    'VALUE_BACKWARD': '',
                    'VALUE_BOTH': '',
                    'VALUE_FORWARD': '',
                    'OUTPUT': f'tmc_algorithms_shortest_path/layer{i}.shp'
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            i = i + 1
            feedback.setProgress(int(i * total))

        container['mergevectorlayers'] = run(
            'native:mergevectorlayers',
            {
                'LAYERS': paths,
                'CRS': QgsProject.instance().crs(),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']
        rmtree('tmc_algorithms_shortest_path')

        if field_flag == 0:
            result['OUTPUT'] = run(
                'native:deletecolumn',
                {
                    'INPUT': container['mergevectorlayers'],
                    'COLUMN': ['layer', 'path'],
                    'OUTPUT': parameters['OUTPUT']
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )['OUTPUT']
            return result

        container['deletecolumn'] = run(
            'native:deletecolumn',
            {
                'INPUT': container['mergevectorlayers'],
                'COLUMN': ['layer', 'path'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']

        container['paths'] = run(
            'native:addautoincrementalfield',
            {
                'INPUT': container['deletecolumn'],
                'FIELD_NAME': 'PATH_ID',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']

        if field_flag in [1, 3]:
            container['source'] = run(
                'native:addautoincrementalfield',
                {
                    'INPUT': source,
                    'FIELD_NAME': 'PATH_ID',
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )['OUTPUT']
            if field_flag == 1:
                container['path_source'] = run(
                    'native:joinattributestable',
                    {
                        'INPUT': container['paths'],
                        'FIELD': 'PATH_ID',
                        'INPUT_2': container['source'],
                        'FIELD_2': 'PATH_ID',
                        'FIELDS_TO_COPY': source_fields,
                        'METHOD': '1',
                        'PREFIX': 'source_',
                        'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True
                )['OUTPUT']
                result['OUTPUT'] = run(
                    'native:deletecolumn',
                    {
                        'INPUT': container['path_source'],
                        'COLUMN': 'PATH_ID',
                        'OUTPUT': parameters['OUTPUT']
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True
                )['OUTPUT']
                return result

            container['path_source'] = run(
                'native:joinattributestable',
                {
                    'INPUT': container['paths'],
                    'FIELD': 'PATH_ID',
                    'INPUT_2': container['source'],
                    'FIELD_2': 'PATH_ID',
                    'FIELDS_TO_COPY': source_fields,
                    'METHOD': '1',
                    'PREFIX': 'source_',
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )['OUTPUT']

        if field_flag in [2, 3]:
            container['destination'] = run(
                'native:addautoincrementalfield',
                {
                    'INPUT': destination,
                    'FIELD_NAME': 'PATH_ID',
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )['OUTPUT']
            if field_flag == 2:
                container['path_destination'] = run(
                    'native:joinattributestable',
                    {
                        'INPUT': container['paths'],
                        'FIELD': 'PATH_ID',
                        'INPUT_2': container['destination'],
                        'FIELD_2': 'PATH_ID',
                        'FIELDS_TO_COPY': destination_fields,
                        'METHOD': '1',
                        'PREFIX': 'destination_',
                        'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True
                )['OUTPUT']
                result['OUTPUT'] = run(
                    'native:deletecolumn',
                    {
                        'INPUT': container['path_destination'],
                        'COLUMN': 'PATH_ID',
                        'OUTPUT': parameters['OUTPUT']
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True
                )['OUTPUT']
                return result

        container['path_complete'] = run(
            'native:joinattributestable',
            {
                'INPUT': container['path_source'],
                'FIELD': 'PATH_ID',
                'INPUT_2': container['destination'],
                'FIELD_2': 'PATH_ID',
                'FIELDS_TO_COPY': destination_fields,
                'METHOD': '1',
                'PREFIX': 'destination_',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']
        result['OUTPUT'] = run(
            'native:deletecolumn',
            {
                'INPUT': container['path_complete'],
                'COLUMN': 'PATH_ID',
                'OUTPUT': parameters['OUTPUT']
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']

        return result

    def name(self):
        return 'Shortest path (point layer to point layer)'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return 'Data Management'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ShortestPathPointLayerAlgorithm()

    def shortHelpString(self):
        return self.tr(
            'This algorithm computes the shortest routes between given start and end points layers.'
        )

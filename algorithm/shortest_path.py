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
from qgis.core import (QgsFeature,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProject)
from shutil import rmtree

def to_feature(integer_list):
    feature = QgsFeature()
    feature.setAttributes(integer_list)
    return feature


class ShortestPathPointLayerAlgorithm(QgsProcessingAlgorithm):

    DESTINATION = 'DESTINATION'
    DESTINATION_FIELDS = 'DESTINATION_FIELDS'
    MANY_TO_MANY = 'MANY_TO_MANY'
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
            QgsProcessingParameterBoolean(
                self.MANY_TO_MANY,
                'Get All Feature Combinations between Source and Destination',
                defaultValue=True
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
        many_to_many = self.parameterAsBool(parameters, self.MANY_TO_MANY, context)
        road = self.parameterAsVectorLayer(parameters, self.ROAD, context)
        source = self.parameterAsVectorLayer(parameters, self.SOURCE, context)
        source_fields = self.parameterAsFields(parameters, self.SOURCE_FIELDS, context)

        field_flag = 0
        if (len(destination_fields) > 0):
            field_flag += 2
        if (len(source_fields) > 0):
            field_flag += 1

        if destination.featureCount() > source.featureCount() and not many_to_many:
            raise Exception('Destination has more data than the source.')
        if destination.featureCount() < source.featureCount() and not many_to_many:
            raise Exception('Souce has more data than the destination.')
        if not destination.featureCount():
            raise Exception('No features present in point layers.')
        if (destination.sourceCrs().authid() != road.sourceCrs().authid()):
            raise Exception('Source and road network CRS do not match.')
        if (destination.sourceCrs().authid() != source.sourceCrs().authid()):
            raise Exception('Source and destination CRS do not match.')

        if path.exists('tmc_algorithms_shortest_path'):
            rmtree('tmc_algorithms_shortest_path')
        mkdir('tmc_algorithms_shortest_path')

        destination_features = destination.getFeatures()
        source_features = source.getFeatures()
        paths = []
        container = {}
        result = {}
        i = 0

        if many_to_many:
            total = 100.0 / (source.featureCount() * destination.featureCount())
            j = 0
            progress = 0
            destination_feature_list = [destination_feature for destination_feature in destination_features]
            source_feature_list = [source_feature for source_feature in source_features]
            for source_feature in source_feature_list:
                if source_feature.hasGeometry():
                    k = 0
                    for destination_feature in destination_feature_list:
                        if feedback.isCanceled():
                            result['OUTPUT'] = None
                            return result
                        if destination_feature.hasGeometry():
                            if not source_feature.geometry().equals(destination_feature.geometry()):
                                file_name = f'tmc_algorithms_shortest_path/layer_{j}_{k}.shp'
                                paths.append(file_name)
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
                                        'OUTPUT': file_name
                                    },
                                    context=context,
                                    feedback=feedback,
                                    is_child_algorithm=True
                                )
                        k += 1
                        progress += 1
                        feedback.setProgress(int(progress * total))
                j += 1

        else:
            total = 100.0 / source.featureCount()
            for destination_feature, source_feature in zip(destination_features, source_features):
                if feedback.isCanceled():
                    result['OUTPUT'] = None
                    return result
                file_name = f'tmc_algorithms_shortest_path/layer_{i}_{i}.shp'
                paths.append(file_name)
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
                        'OUTPUT': file_name
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True
                )
                i += 1
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

        container['path_with_source'] = run(
            'native:fieldcalculator',
            {
                'FIELD_LENGTH': 0,
                'FIELD_NAME': 'SOURCE_ID',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 1, # Integer (32 bit)
                'FORMULA': 'regexp_substr("layer", \'layer_(\\\\d+)\')',
                'INPUT': container['mergevectorlayers'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']

        container['path_with_destination'] = run(
            'native:fieldcalculator',
            {
                'FIELD_LENGTH': 0,
                'FIELD_NAME': 'DESTINATION_ID',
                'FIELD_PRECISION': 0,
                'FIELD_TYPE': 1, # Integer (32 bit)
                'FORMULA': 'regexp_substr("layer", \'layer_\\\\d+_(\\\\d+)\')',
                'INPUT': container['path_with_source'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']

        container['paths'] = run(
            'native:deletecolumn',
            {
                'INPUT': container['path_with_destination'],
                'COLUMN': ['layer', 'path'],
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
                    'FIELD_NAME': 'SOURCE_ID',
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )['OUTPUT']

            container['path_source'] = run(
                'native:joinattributestable',
                {
                    'INPUT': container['paths'],
                    'FIELD': 'SOURCE_ID',
                    'INPUT_2': container['source'],
                    'FIELD_2': 'SOURCE_ID',
                    'FIELDS_TO_COPY': source_fields,
                    'METHOD': '1',
                    'PREFIX': 'source_',
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )['OUTPUT']

            if field_flag == 1:
                result['OUTPUT'] = run(
                    'native:deletecolumn',
                    {
                        'INPUT': container['path_source'],
                        'COLUMN': ['DESTINATION_ID', 'SOURCE_ID'],
                        'OUTPUT': parameters['OUTPUT']
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True
                )['OUTPUT']
                return result

        if field_flag in [2, 3]:
            container['destination'] = run(
                'native:addautoincrementalfield',
                {
                    'INPUT': destination,
                    'FIELD_NAME': 'DESTINATION_ID',
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
                        'FIELD': 'DESTINATION_ID',
                        'INPUT_2': container['destination'],
                        'FIELD_2': 'DESTINATION_ID',
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
                        'COLUMN': ['DESTINATION_ID', 'SOURCE_ID'],
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
                'FIELD': 'DESTINATION_ID',
                'INPUT_2': container['destination'],
                'FIELD_2': 'DESTINATION_ID',
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
                'COLUMN': ['DESTINATION_ID', 'SOURCE_ID'],
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

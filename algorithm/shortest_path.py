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
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterString,
                       QgsProject)
from shutil import rmtree

def to_feature(integer_list):
    feature = QgsFeature()
    feature.setAttributes(integer_list)
    return feature


class ShortestPathPointLayerAlgorithm(QgsProcessingAlgorithm):

    DEFAULT_DIRECTION = 'DEFAULT_DIRECTION'
    DEFAULT_SPEED = 'DEFAULT_SPEED'
    DEM = 'DEM'
    DESTINATION = 'DESTINATION'
    DESTINATION_FIELDS = 'DESTINATION_FIELDS'
    DIRECTION_FIELD = 'DIRECTION_FIELD'
    MANY_TO_MANY = 'MANY_TO_MANY'
    OUTPUT = 'OUTPUT'
    ROAD = 'ROAD'
    SOURCE = 'SOURCE'
    SOURCE_FIELDS = 'SOURCE_FIELDS'
    SPEED_FIELD = 'SPEED_FIELD'
    STRATEGY = 'STRATEGY'
    VALUE_BACKWARD = 'VALUE_BACKWARD'
    VALUE_BOTH = 'VALUE_BOTH'
    VALUE_FORWARD = 'VALUE_FORWARD'

    def initAlgorithm(self, config):
        par_default_direction = QgsProcessingParameterEnum(
            self.DEFAULT_DIRECTION,
            self.tr('Default direction'),
            options=[
                self.tr('Forward direction'),
                self.tr('Backward direction'),
                self.tr('Both directions')
            ],
            defaultValue=2
        )
        par_default_speed = QgsProcessingParameterNumber(
            self.DEFAULT_SPEED,
            self.tr('Default speed (km/h)'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=50,
            minValue=0
        )
        par_direction_field = QgsProcessingParameterField(
            self.DIRECTION_FIELD,
            self.tr('Direction field'),
            parentLayerParameterName=self.ROAD,
            optional=True
        )
        par_speed_field = QgsProcessingParameterField(
            self.SPEED_FIELD,
            self.tr('Speed field'),
            parentLayerParameterName=self.ROAD,
            optional=True
        )
        par_strategy = QgsProcessingParameterEnum(
            self.STRATEGY,
            self.tr('Path type to calculate'),
            options=[
                self.tr('Shortest'),
                self.tr('Fastest')
            ],
            defaultValue=0
        )
        par_value_backward = QgsProcessingParameterString(
            self.VALUE_BACKWARD,
            self.tr('Value for backward direction'),
            defaultValue='',
            optional=True
        )
        par_value_both = QgsProcessingParameterString(
            self.VALUE_BOTH,
            self.tr('Value for both directions'),
            defaultValue='',
            optional=True
        )
        par_value_forward = QgsProcessingParameterString(
            self.VALUE_FORWARD,
            self.tr('Value for forward direction'),
            defaultValue='',
            optional=True
        )
        par_default_direction.setFlags(par_default_direction.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        par_default_speed.setFlags(par_default_speed.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        par_direction_field.setFlags(par_direction_field.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        par_speed_field.setFlags(par_speed_field.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        par_strategy.setFlags(par_strategy.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        par_value_backward.setFlags(par_value_backward.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        par_value_both.setFlags(par_value_both.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        par_value_forward.setFlags(par_value_forward.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

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
                self.tr('Source table columns to be copied'),
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
                self.tr('Destination table columns to be copied'),
                parentLayerParameterName=self.DESTINATION,
                allowMultiple=True,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.MANY_TO_MANY,
                self.tr('Get all feature combinations between source and destination'),
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
            QgsProcessingParameterRasterLayer(
                self.DEM,
                self.tr('Raster DEM Layer'),
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )
        self.addParameter(par_strategy)
        self.addParameter(par_direction_field)
        self.addParameter(par_value_forward)
        self.addParameter(par_value_backward)
        self.addParameter(par_value_both)
        self.addParameter(par_default_direction)
        self.addParameter(par_speed_field)
        self.addParameter(par_default_speed)

    def processAlgorithm(self, parameters, context, feedback):
        default_direction = self.parameterAsEnum(parameters, self.DEFAULT_DIRECTION, context)
        default_speed = self.parameterAsDouble(parameters, self.DEFAULT_SPEED, context)
        dem = self.parameterAsRasterLayer(parameters, self.DEM, context)
        destination = self.parameterAsVectorLayer(parameters, self.DESTINATION, context)
        destination_fields = self.parameterAsFields(parameters, self.DESTINATION_FIELDS, context)
        direction_field = self.parameterAsFields(parameters, self.DIRECTION_FIELD, context) or ''
        many_to_many = self.parameterAsBool(parameters, self.MANY_TO_MANY, context)
        road = self.parameterAsVectorLayer(parameters, self.ROAD, context)
        source = self.parameterAsVectorLayer(parameters, self.SOURCE, context)
        source_fields = self.parameterAsFields(parameters, self.SOURCE_FIELDS, context)
        speed_field = self.parameterAsFields(parameters, self.SPEED_FIELD, context) or ''
        strategy = self.parameterAsEnum(parameters, self.STRATEGY, context)
        value_backward = self.parameterAsString(parameters, self.VALUE_BACKWARD, context)
        value_both = self.parameterAsString(parameters, self.VALUE_BOTH, context)
        value_forward = self.parameterAsString(parameters, self.VALUE_FORWARD, context)

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
                                        'DEFAULT_DIRECTION': default_direction,
                                        'DEFAULT_SPEED': default_speed,
                                        'DIRECTION_FIELD': direction_field,
                                        'END_POINT': destination_feature.geometry(),
                                        'INPUT': parameters[self.ROAD],
                                        'SPEED_FIELD': speed_field,
                                        'START_POINT': source_feature.geometry(),
                                        'STRATEGY': strategy,
                                        'TOLERANCE': 0,
                                        'VALUE_BACKWARD': value_backward,
                                        'VALUE_BOTH': value_both,
                                        'VALUE_FORWARD': value_forward,
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
                        'DEFAULT_DIRECTION': default_direction,
                        'DEFAULT_SPEED': default_speed,
                        'DIRECTION_FIELD': direction_field,
                        'END_POINT': destination_feature.geometry(),
                        'INPUT': parameters[self.ROAD],
                        'SPEED_FIELD': speed_field,
                        'START_POINT': source_feature.geometry(),
                        'STRATEGY': strategy,
                        'TOLERANCE': 0,
                        'VALUE_BACKWARD': value_backward,
                        'VALUE_BOTH': value_both,
                        'VALUE_FORWARD': value_forward,
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
            container['multi'] = run(
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

        else:
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
                    container['multi'] = run(
                        'native:deletecolumn',
                        {
                            'INPUT': container['path_source'],
                            'COLUMN': ['DESTINATION_ID', 'SOURCE_ID'],
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

                    container['multi'] = run(
                        'native:deletecolumn',
                        {
                            'INPUT': container['path_destination'],
                            'COLUMN': ['DESTINATION_ID', 'SOURCE_ID'],
                            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                        },
                        context=context,
                        feedback=feedback,
                        is_child_algorithm=True
                    )['OUTPUT']

            if field_flag == 3:
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

                container['multi'] = run(
                    'native:deletecolumn',
                    {
                        'INPUT': container['path_complete'],
                        'COLUMN': ['DESTINATION_ID', 'SOURCE_ID'],
                        'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                    },
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True
                )['OUTPUT']

        container['single'] = run(
            'native:multiparttosingleparts',
            {
                'INPUT': container['multi'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']

        if not dem:
            result['OUTPUT'] = run(
                'native:fieldcalculator',
                {
                    'FIELD_LENGTH': 0,
                    'FIELD_NAME': 'distance_2d_km',
                    'FIELD_PRECISION': 3,
                    'FIELD_TYPE': 0,
                    'FORMULA': 'length3D($geometry) / 1000',
                    'INPUT': container['single'],
                    'OUTPUT': parameters['OUTPUT']
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )['OUTPUT']

            return result

        container['2d'] = run(
            'native:fieldcalculator',
            {
                'FIELD_LENGTH': 0,
                'FIELD_NAME': 'distance_2d_km',
                'FIELD_PRECISION': 3,
                'FIELD_TYPE': 0,
                'FORMULA': 'length3D($geometry) / 1000',
                'INPUT': container['single'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']

        container['3d'] = run(
            'native:setzfromraster',
            {
                'BAND': 1,
                'INPUT': container['2d'],
                'NODATA': 0,
                'RASTER': parameters[self.DEM],
                'SCALE': 1,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']

        result['OUTPUT'] = run(
            'native:fieldcalculator',
            {
                'FIELD_LENGTH': 0,
                'FIELD_NAME': 'distance_3d_km',
                'FIELD_PRECISION': 3,
                'FIELD_TYPE': 0,
                'FORMULA': 'length3D($geometry) / 1000',
                'INPUT': container['3d'],
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

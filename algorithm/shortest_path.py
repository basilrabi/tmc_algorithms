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

from os import mkdir
from processing import run # pyright: reportMissingImports=false
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProject)
from shutil import rmtree

class ShortestPathPointLayerAlgorithm(QgsProcessingAlgorithm):

    DESTINATION = 'DESTINATION'
    OUTPUT = 'OUTPUT'
    ROAD = 'ROAD'
    SOURCE = 'SOURCE'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SOURCE,
                self.tr('Source Point Layer'),
                [QgsProcessing.TypeVectorPoint]
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
        road = self.parameterAsVectorLayer(parameters, self.ROAD, context)
        source = self.parameterAsVectorLayer(parameters, self.SOURCE, context)
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
        mkdir('tmc_algorithms_shortest_path')
        paths = []
        results = {}
        i = 0
        for destination_feature, source_feature in zip(destination_features, source_features):
            if feedback.isCanceled():
                break

            alg_params = {
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
            }
            paths.append(f'tmc_algorithms_shortest_path/layer{i}.shp')
            run(
                'native:shortestpathpointtopoint',
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            i = i + 1
            feedback.setProgress(int(i * total))

        alg_params = {
            'LAYERS': paths,
            'CRS': QgsProject.instance().crs(),
            'OUTPUT': parameters['OUTPUT']
        }
        results['OUTPUT'] = run(
            'native:mergevectorlayers',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )['OUTPUT']
        rmtree('tmc_algorithms_shortest_path')

        return results

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

# -*- coding: utf-8 -*-

"""
/***************************************************************************
 MtspSolver
                                 A QGIS plugin
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-02-16
        copyright            : (C) 2022 by Boris Karpov
        email                : bkarpov96@ya.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Boris Karpov'
__date__ = '2022-02-16'
__copyright__ = '(C) 2022 by Boris Karpov'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis import core
from qgis.PyQt import QtCore
from routing import solution as sl
from routing import spatial_objects as sp


class MtspRouting(core.QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    DEST_LAYER = "DEST_LAYER"
    ROADS_LAYER = "ROADS_LAYER"
    NUMBER_OF_ROUTES = "NUMBER_OF_ROUTES"
    RESULT = "RESULT"

    def __init__(self):
        super(MtspRouting, self).__init__()

        locale_path = os.path.join(
            os.path.dirname(__file__),
            "i18n",
            f"{os.path.splitext(os.path.basename(__file__))[0]}_{QtCore.QSettings().value('locale/userLocale')[:2]}.qm"
        )

        if os.path.exists(locale_path):
            self.translator = QtCore.QTranslator()
            self.translator.load(locale_path)
            QtCore.QCoreApplication.installTranslator(self.translator)

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            core.QgsProcessingParameterFeatureSource(
                self.DEST_LAYER,
                self.tr("Destinations"),
                [core.QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            core.QgsProcessingParameterFeatureSource(
                self.ROADS_LAYER,
                self.tr("Roads"),
                [core.QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            core.QgsProcessingParameterNumber(
                self.NUMBER_OF_ROUTES,
                self.tr("Number of routes"),
                minValue=1,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Получить данные, выбранные пользователем
        destinations_layer = self.parameterAsLayer(parameters, self.DEST_LAYER, context)
        roads_layer = self.parameterAsLayer(parameters, self.ROADS_LAYER, context)
        number_of_routes = self.parameterAsInt(parameters, self.NUMBER_OF_ROUTES, context)

        # Преобразовать данные для использования в алгоритмах mtsp-routing-core
        points = []

        qgis_objects_attributes = {}  # Атрибуты исходных объектов
        # Атрибуты вынесены в словарь, тк они содержат Qgis объекты, несовместимые с multiprocessing

        for feature in destinations_layer.getFeatures():
            geom = feature.geometry().asPoint()
            point = sp.Point(geom[0], geom[1])
            qgis_objects_attributes[point] = feature.attributes()
            points.append(point)

        graph = sp.Graph()

        for feature in roads_layer.getFeatures():
            geom = feature.geometry().asPolyline()

            for i in range(len(geom) - 1):  # Если отрезок состоит из 3 и более точек, то он добавляется по частям
                edge = sp.Segment(
                    sp.Point(geom[i][0], geom[i][1]),
                    sp.Point(geom[i + 1][0], geom[i + 1][1]),
                )

                qgis_objects_attributes[edge] = feature.attributes()
                graph.add_edge(edge)

        # Подсчитать результат
        results = sl.build_routes(points, number_of_routes, graph)

        # Создать новые слои с дополнительными атрибутами
        res_atts = [
            core.QgsField("route_id", QtCore.QVariant.Int),  # Номер маршрута
            core.QgsField("number_in_route", QtCore.QVariant.Int)  # Порядковый номер внутри маршрута
        ]

        clustered_destinations_layer = core.QgsVectorLayer("Point", "destinations", "memory")
        clustered_destinations_data = clustered_destinations_layer.dataProvider()
        clustered_destinations_data.addAttributes(destinations_layer.dataProvider().fields().toList() + res_atts)
        clustered_destinations_layer.updateFields()

        routes_layer = core.QgsVectorLayer("LineString", "routes", "memory")
        routes_layer_data = routes_layer.dataProvider()
        routes_layer_data.addAttributes(roads_layer.dataProvider().fields().toList() + res_atts)
        routes_layer.updateFields()

        # Создать объекты на новых слоях
        for cluster_idx, result in enumerate(results):
            cluster, route = result

            for point_idx, point in enumerate(cluster):
                new_feature = core.QgsFeature()
                new_feature.setGeometry(core.QgsGeometry.fromPointXY(core.QgsPointXY(point.x, point.y)))
                new_feature.setAttributes(qgis_objects_attributes[point] + [cluster_idx + 1, point_idx + 1])
                clustered_destinations_data.addFeature(new_feature)

            for edge_idx, edge in enumerate(route):
                new_feature = core.QgsFeature()
                new_feature.setGeometry(
                    core.QgsGeometry.fromPolyline(
                        [core.QgsPoint(point.x, point.y) for point in (edge.start, edge.finish)]
                    )
                )
                new_feature.setAttributes(qgis_objects_attributes[edge] + [cluster_idx + 1, edge_idx + 1])
                routes_layer_data.addFeature(new_feature)

        # Добавить слои в проект
        layer_details = core.QgsProcessingContext.LayerDetails("", core.QgsProject.instance(), "")

        context.temporaryLayerStore().addMapLayers([clustered_destinations_layer, routes_layer])
        context.setLayersToLoadOnCompletion({
            clustered_destinations_layer.id(): layer_details,
            routes_layer.id(): layer_details,
        })

        return {self.RESULT: (clustered_destinations_layer, routes_layer)}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "Build routes"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "Routing"

    def tr(self, string):
        return QtCore.QCoreApplication.translate(self.__class__.__name__, string)

    def createInstance(self):
        return MtspRouting()

    def shortHelpString(self):
        return self.tr("""
        Solve the multiple traveling salesman problem (MTSP).
        Divide the points into clusters of the same size and build routes in them.

        Parameters:
            Destinations: Layer with destinations. All points must be reachable by roads.
            Roads: Layer with roads. It's strongly recommended to divide roads by roads before running the algorithm.
            Number of routes: Number of routes to build.
        """)

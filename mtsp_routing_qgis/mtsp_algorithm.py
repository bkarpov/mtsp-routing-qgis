# coding: utf-8
"""Алгоритм решения MTSP"""

from __future__ import annotations

import os
from typing import Any, Iterator

from qgis import core
from qgis.PyQt import QtCore
from routing import solution as sl
from routing import spatial_objects as sp

__author__ = "Boris Karpov"
__date__ = "2022-02-16"
__copyright__ = "(C) 2022 by Boris Karpov"
__revision__ = "$Format:%H$"


class MtspRouting(core.QgsProcessingAlgorithm):
    """Алгоритм решения MTSP"""

    # Ключи параметров входных данных и результата
    DEST_LAYER = "DEST_LAYER"
    ROADS_LAYER = "ROADS_LAYER"
    NUMBER_OF_ROUTES = "NUMBER_OF_ROUTES"
    NUMBER_OF_PROCESSES = "NUMBER_OF_PROCESSES"
    RESULT = "RESULT"

    def __init__(self) -> None:
        """Конструктор

        К алгоритму подключается QTranslator, использующий перевод из директории i18n"""

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

    def initAlgorithm(self, config: Any) -> None:
        """Добавить параметры в окно алгоритма"""

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
                self.tr("Road network"),
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

        self.addParameter(
            core.QgsProcessingParameterNumber(
                self.NUMBER_OF_PROCESSES,
                self.tr("Number of processes"),
                defaultValue=os.cpu_count(),
                minValue=1,
                maxValue=os.cpu_count(),
            )
        )

    def processAlgorithm(
            self,
            parameters: dict[str, Any],
            context: core.QgsProcessingContext,
            feedback: Any
    ) -> dict[str, tuple]:
        """Решить MTSP

        Результат 2 слоя - destinations и routes
        - Слои автоматически добавляются в проект
        - Слои сохраняют атрибуты исходных слоев с пунктами назначения и дорожной сетью и добавляют 2 новых
        - - Новые атрибуты: route_id - идентификатор маршрута, number_in_route - номер объекта в пределах маршрута
        - Объекты сохраняют значения исходных атрибутов

        Слои, выбранные в качестве параметров, не меняются

        Args:
            parameters: Параметры, выбранные при запуске алгоритма в QGIS
            context: Объект для работы с текущим проектом
            feedback: Объект для отправки оповещений в окно алгоритма

        Returns:
            Словарь {ключ результата: кортеж с объектами слоев destinations и routes}
        """

        # Подготовить входные данные
        number_of_routes = self.parameterAsInt(parameters, self.NUMBER_OF_ROUTES, context)
        number_of_processes = self.parameterAsInt(parameters, self.NUMBER_OF_PROCESSES, context)
        points, graph, qgis_objects_attributes = self._prepare_data(parameters, context)

        results = sl.build_routes(points, number_of_routes, graph, number_of_processes)  # Подсчитать результат

        # Сохранить результат
        dest_layer, routes_layer = self._save_result(parameters, context, qgis_objects_attributes, results)

        return {self.RESULT: (dest_layer, routes_layer)}

    def _prepare_data(
            self,
            parameters: dict[str, Any],
            context: core.QgsProcessingContext
    ) -> tuple[list[sp.Point], sp.Graph, dict]:
        """Подготовить список пунктов назначений и граф с дорожной сетью для решения MTSP

        Args:
            parameters: Параметры, выбранные при запуске алгоритма в QGIS
            context: Объект для работы с текущим проектом

        Returns:
            Кортеж, содержащий список точек, граф с дорожной сетью, словарь с атрибутами исходных объектов
        """

        # Получить слои, выбранные пользователем
        dest_layer = self.parameterAsLayer(parameters, self.DEST_LAYER, context)
        roads_layer = self.parameterAsLayer(parameters, self.ROADS_LAYER, context)

        # Преобразовать данные для использования в алгоритмах mtsp-routing-core
        points = []

        qgis_objects_attributes = {}  # Атрибуты исходных объектов
        # Атрибуты вынесены в словарь, тк они содержат Qgis объекты, несовместимые с multiprocessing

        for feature in dest_layer.getFeatures():
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
                    sp.Point(geom[i + 1][0], geom[i + 1][1])
                )

                qgis_objects_attributes[edge] = feature.attributes()
                graph.add_edge(edge)

        return points, graph, qgis_objects_attributes

    def _save_result(
            self,
            parameters: dict[str, Any],
            context: core.QgsProcessingContext,
            qgis_objects_attributes: dict,
            results: Iterator[tuple[list[sp.Point], list[sp.Segment]]]
    ) -> tuple[core.QgsVectorLayer, core.QgsVectorLayer]:
        """Сохранить результат решения MTSP в QGIS проект

        Результат выводится в виде 2 слоев - destinations и routes

        Args:
            parameters: Параметры, выбранные при запуске алгоритма в QGIS
            context: Объект для работы с проектом
            qgis_objects_attributes: Словарь атрибутов пунктов назначения и ребер графа
            results: Результат решения MTSP

        Returns:
            Кортеж со слоями с ответом
        """

        # Получить слои, выбранные пользователем
        dest_source = self.parameterAsLayer(parameters, self.DEST_LAYER, context)
        roads_source = self.parameterAsLayer(parameters, self.ROADS_LAYER, context)

        # Создать новые слои с дополнительными атрибутами
        res_atts = [
            core.QgsField("route_id", QtCore.QVariant.Int),  # Номер маршрута
            core.QgsField("number_in_route", QtCore.QVariant.Int),  # Порядковый номер внутри маршрута
        ]

        def create_layer(geom_type: str, name: str, source_layer: core.QgsVectorLayer) -> tuple:
            """Создать слой и объект, для работы с данными слоя"""

            layer = core.QgsVectorLayer(geom_type, name, "memory")
            layer_data_provider = layer.dataProvider()
            layer_data_provider.addAttributes(source_layer.dataProvider().fields().toList() + res_atts)
            layer.updateFields()

            return layer, layer_data_provider

        dest_res, dest_res_data = create_layer("Point", "destinations", dest_source)
        roads_res, roads_res_data = create_layer("LineString", "routes", roads_source)

        # Создать объекты на новых слоях
        for cluster_idx, result in enumerate(results):
            cluster, route = result

            for point_idx, point in enumerate(cluster):
                new_feature = core.QgsFeature()
                new_feature.setGeometry(core.QgsGeometry.fromPointXY(core.QgsPointXY(point.x, point.y)))
                new_feature.setAttributes(qgis_objects_attributes[point] + [cluster_idx + 1, point_idx + 1])
                dest_res_data.addFeature(new_feature)

            for edge_idx, edge in enumerate(route):
                new_feature = core.QgsFeature()
                polyline_points = [core.QgsPoint(point.x, point.y) for point in (edge.start, edge.finish)]
                new_feature.setGeometry(core.QgsGeometry.fromPolyline(polyline_points))
                new_feature.setAttributes(qgis_objects_attributes[edge] + [cluster_idx + 1, edge_idx + 1])
                roads_res_data.addFeature(new_feature)

        # Добавить слои в проект
        layer_details = core.QgsProcessingContext.LayerDetails("", core.QgsProject.instance(), "")

        context.temporaryLayerStore().addMapLayers([dest_res, roads_res])
        context.setLayersToLoadOnCompletion({
            dest_res.id(): layer_details,
            roads_res.id(): layer_details,
        })

        return dest_res, roads_res

    def name(self) -> str:
        return "Build routes"

    def displayName(self) -> str:
        return self.tr(self.name())

    def groupId(self) -> str:
        return "Routing"

    def group(self) -> str:
        return self.tr(self.groupId())

    def tr(self, string: str) -> str:
        """Перевести строку

        Args:
            string: Строка, которую нужно перевести

        Returns:
            Строка, переведенная на язык текущей локали, если такой перевод существует, иначе иходная строка
        """

        return QtCore.QCoreApplication.translate(self.__class__.__name__, string)

    def createInstance(self) -> MtspRouting:
        return MtspRouting()

    def shortHelpString(self) -> str:
        """Получить подробное описание алгоритма

        Выводится в окне алгоритма"""

        return self.tr("""
        Solve the multiple traveling salesman problem (MTSP).
        Divide the points into clusters of the same size and build routes in them.

        Parameters:
            Destinations: Layer with destinations. All points must be reachable by roads.
            Road network: Layer with roads.
            Number of routes: Number of routes to build.
            Number of processes: Number of processes for parallel route building.
                The maximum number of processes is equal to the number of logical processors.
                The more processes are used, the faster routes are built.

        <a href="https://github.com/bkarpov/mtsp-routing-qgis/blob/main/README.md">Manual</a>
        """)

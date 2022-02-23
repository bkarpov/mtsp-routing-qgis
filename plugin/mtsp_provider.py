# coding: utf-8
"""Класс обработчика, инициализирующий и выводящий алгоритмы в интерфейс"""

from qgis import core

from plugin.mtsp_algorithm import MtspRouting

__author__ = "Boris Karpov"
__date__ = "2022-02-16"
__copyright__ = "(C) 2022 by Boris Karpov"
__revision__ = "$Format:%H$"


class MtspRoutingProvider(core.QgsProcessingProvider):
    """Класс обработчика, инициализирующий и выводящий алгоритмы в интерфейс"""

    def __init__(self) -> None:
        core.QgsProcessingProvider.__init__(self)

    def unload(self) -> None:
        pass

    def loadAlgorithms(self) -> None:
        """Загрузить алгоритмы в Processing Toolbox"""

        self.addAlgorithm(MtspRouting())

    def id(self) -> str:
        return "MtspRouting"

    def name(self):
        return "MTSP Routing"

    def icon(self):
        return core.QgsProcessingProvider.icon(self)

    def longName(self):
        return self.name()

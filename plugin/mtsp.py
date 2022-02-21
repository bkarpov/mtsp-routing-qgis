# coding: utf-8
"""Плагин для решения MTSP"""

import inspect
import os
import sys

from qgis import core

from plugin.mtsp_provider import MtspRoutingProvider

__author__ = "Boris Karpov"
__date__ = "2022-02-16"
__copyright__ = "(C) 2022 by Boris Karpov"
__revision__ = "$Format:%H$"

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class MtspRoutingPlugin:
    """Класс плагина"""

    def __init__(self) -> None:
        self.provider = None

    def initProcessing(self) -> None:
        """Добавить обработчик в Processing Toolbox

        С помощью обработчика добавляются отдельные алгоритмы"""

        self.provider = MtspRoutingProvider()
        core.QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self) -> None:
        self.initProcessing()

    def unload(self) -> None:
        core.QgsApplication.processingRegistry().removeProvider(self.provider)

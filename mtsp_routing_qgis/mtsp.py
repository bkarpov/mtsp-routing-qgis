# coding: utf-8
"""Плагин для решения MTSP"""

import inspect
import multiprocessing
import os
import sys

from PyQt5 import QtCore
from qgis import core

from mtsp_routing_qgis.mtsp_provider import MtspRoutingProvider

__author__ = "Boris Karpov"
__date__ = "2022-02-16"
__copyright__ = "(C) 2022 by Boris Karpov"
__revision__ = "$Format:%H$"

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

if os.name == "nt":  # Исправления для запуска на Windows
    if not hasattr(sys, "argv"):  # Почему-то у sys отсутствует атрибут argv
        sys.argv = [""]

    # Явно указать запускаемый файл для создания подпроцессов
    multiprocessing.set_executable(QtCore.QStandardPaths.findExecutable("python"))
    # По умолчанию вместо подпроцесса с python запускается новый процесс с QGIS


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

# coding: utf-8
"""Инициализация плагина в QGIS"""

__author__ = 'Boris Karpov'
__date__ = '2022-02-16'
__copyright__ = '(C) 2022 by Boris Karpov'


from qgis import gui

from plugin.mtsp import MtspRoutingPlugin


# noinspection PyPep8Naming
def classFactory(iface: gui.QgisInterface) -> MtspRoutingPlugin:  # pylint: disable=invalid-name
    """Загрузить класс MtspRoutingPlugin"""

    return MtspRoutingPlugin()

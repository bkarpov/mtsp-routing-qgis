# mtsp-routing-qgis

[EN](https://github.com/bkarpov/mtsp-routing-qgis/blob/main/README.md)

Плагин для QGIS для решения multiple traveling salesman problem (MTSP).

Вычисления выполняются пакетом mtsp-routing-core
([GitHub](https://github.com/bkarpov/mtsp-routing-core),
[PyPI](https://pypi.org/project/mtsp-routing/)), не привязанным к какой-либо ГИС.

---

## Установка

### I. Установка Python пакета mtsp-routing

Пакет нужен для выполнения вычислений, без него плагин QGIS не сможет работать. 

#### Установка в QGIS
1. Открыть консоль Python
2. Выполнить команды
```python
import pip
pip.main(["install", "mtsp-routing"])
```
 
#### Установка через терминал в Linux

Открыть терминал и выполнить команду ```python -m pip install mtsp-routing```

#### Установка через терминал в Windows

Открыть терминал OSGeo4W (устанавливается вместе с QGIS) и выполнить команду ```python -m pip install mtsp-routing```

### II. Установка QGIS плагина "MTSP Routing"

Модули / Управление и установка модулей
![Установка плагина "MTSP Routing"](docs/images/ru/installation.png)

---

## Пример

### 1. Подготовить данные
   1. Добавить карту OSM из плагина QuickMapServices
![Выпадающее меню плагина плагина QuickMapServices](docs/images/ru/data_preparation_1.png)
   2. Создать полигон с зоной доставки
![Полигон с зоной доставки](docs/images/ru/data_preparation_2.png)
   3. Выгрузить дороги, входящие в зону доставки с помощью плагина QuickOSM
      1. Вектор / QuickOSM / QuickOSM
![Окно плагина QuickOSM](docs/images/ru/data_preparation_3.png)
![Проект с выгруженными дорогами](docs/images/ru/data_preparation_4.png)
   4. Добавить слой с пунктами назначения
![Проект с добавленными пунктами назначения](docs/images/ru/data_preparation_5.png)
   5. Подключить пункты назначения к дорожной сети с помощью плагина GRASS
      1. Инструменты анализа / GRASS / Инструменты обработки векторных данных / v.net
![Окно алгоритма GRASS v.net](docs/images/ru/data_preparation_6.png)
![Дорожная сеть с подключенными пунктами назначения](docs/images/ru/data_preparation_7.png)

### 2. Запустить алгоритм
![Запуск построения маршрутов](docs/images/ru/run_algorithm.png)

### 3. Настроить отображение результата
   1. Классифицировать пункты назначения по атрибуту route_id
![Настройка стилей для слоя с пунктами назначения](docs/images/ru/output_settings_1.png)
   2. Добавить подписи к пунктам назначения
![Добавление подписей к пунктам назначения](docs/images/ru/output_settings_2.png)
   3. Классифицировать использованные дороги по атрибуту route_id
![Настройка стилей для слоя с использованными дорогами](docs/images/ru/output_settings_3.png)
   4. Добавить подписи к использованным участкам дорог
      1. Чтобы подписи не сливались в 1 число, использовать выражение с добавлением разделителя 
![Добавление подписей к дорогам](docs/images/ru/output_settings_4.png)

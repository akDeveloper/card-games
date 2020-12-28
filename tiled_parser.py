import json
from pygame import Rect
from typing import Optional


class TileItem(object):
    def __init__(self, rect: Rect, id: int, ttype: str = None):
        self.__id = id
        self.__rect = rect
        self.__type = ttype

    def get_rect(self) -> Rect:
        return self.__rect

    def get_id(self) -> int:
        return self.__id

    def get_type(self) -> Optional[str]:
        return self.__type


class TileLayer(object):
    def __init__(self, name: str, config: dict, tile: Rect):
        self.__items = []
        self.width = int(config['width'] * tile.width)
        self.height = int(config['height'] * tile.height)
        self.__name: str = name
        self.__properties: str = self.__parse_type(config['properties'])
        x: int = 0
        y: int = 0
        index: int = 0
        for item in config['data']:
            if item != 0:
                index += 1
                rect = Rect(x * tile.width,
                            y * tile.height,
                            tile.width,
                            tile.height)
                self.__items.append(
                    TileItem(rect, item, self.get_type())
                )
            x += 1
            if x > config['width'] - 1:
                x = 0
                y += 1

    def get_name(self) -> str:
        return self.__name

    def get_items(self) -> list:
        return self.__items

    def get_type(self) -> str:
        return self.__properties.get('tile_type')

    def is_actor(self) -> bool:
        return self.__properties.get('is_actor')

    def get_properties(self) -> dict:
        return self.__properties

    def __parse_type(self, properties: list) -> dict:
        props = {}
        for i in properties:
            props[i.get('name')] = i.get('value')
        return props


class ObjectGroup(object):
    def __init__(self, config: dict):
        self.__items: list = []
        self.__name: str = config['name']
        for item in config['objects']:
            if item['visible'] is False:
                continue
            rect = Rect(item['x'], item['y'], item['width'], item['height'])
            self.__items.append(TileItem(rect, item['id'], item['type']))

    def get_items(self) -> list:
        return self.__items

    def get_name(self) -> str:
        return self.__name

    def get_type(self) -> str:
        return 'object'

    def is_actor(self) -> bool:
        return False


class Map(object):
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.__layers = []
        self.__screen: Rect = None

    def add_layer(self, layer: object) -> None:
        self.__layers.append(layer)

    def set_screen(self, screen: Rect) -> None:
        self.__screen = screen

    def get_screen(self) -> Rect:
        return self.__screen

    def get_layers(self) -> list:
        return self.__layers

    def get_object_group(self, name: str) -> Optional[ObjectGroup]:
        for i in self.__layers:
            if i.get_name() == name:
                return i
        return None

    def get_rect(self) -> Rect:
        return Rect(0, 0, self.width, self.height)


class TiledParser(object):
    def __init__(self, file: str):
        self.layers = []
        with open(file) as f:
            data = json.load(f)
        width = data['width'] * data['tilewidth']
        height = data['height'] * data['tileheight']
        self.__map = Map(width, height)
        tile = Rect(0, 0, data['tilewidth'], data['tileheight'])
        for layer in data['layers']:
            if layer['visible'] is False:
                continue
            if layer['type'] == 'tilelayer':
                self.__map.add_layer(TileLayer(layer['name'], layer, tile))
            if layer['type'] == 'objectgroup':
                self.__map.add_layer(ObjectGroup(layer))

    def get_map(self) -> Map:
        return self.__map

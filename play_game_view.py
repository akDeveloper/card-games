from tiled_parser import Map
from cards import Player, Table

class PlayGameView(object):
    def __init__(self, map: Map, actor: Player, cpu: Player, table: Table):
        self.map: Map = map
        self.actor = actor
        self.cpu = cpu
        self.table = table

    def render(self, surface) -> None:
        surface.fill((0, 38, 0))
        self.actor.draw(surface)
        self.cpu.draw(surface)
        self.table.draw(surface)

    def blit_debug(self) -> None:
        pass

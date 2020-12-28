from __future__ import annotations
from play_game_view import PlayGameView
from pygame import Rect, Surface
from graphics import Graphics
from cards import DeckOfCards, Card, Player, Table, Cpu
from pygame.sprite import Group
from tiled_parser import TiledParser, Map
from pygame.event import Event

class Timer(object):
    def __init__(self, delay: int):
        self.delay: int = delay
        self.counter: int = 0

    def completed(self, time: int):
        self.counter += time
        if self.counter >= self.delay:
            return True
        return False

    def looped(self, time: int):
        self.counter += time
        if self.counter >= self.delay:
            self.counter = 0
            return True
        return False

class Game(object):
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600

    def __init__(self):
        self.graphics = Graphics(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        screen_rect = Rect(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.__debug = False
        self.state = PlayGameState(screen_rect)
        self.mouse_event = None

    def update(self, time: int) -> None:
        """ Get the next state of the game """
        self.state = self.state.get_state()
        """ Update the state of sprites, level, etc """
        self.state.update(time, self.mouse_event)

    def on_mouse_up(self, event):
        self.mouse_event = event

    def render(self) -> None:
        self.state.render(self.graphics.get_surface())
        self.graphics.render()

    def toggle_debug(self) -> None:
        self.state.toggle_debug()


class GameState(object):
    def __init__(self):
        raise RuntimeError("Can not instatiate")

    def update(self, time: int) -> None:
        raise NotImplementedError("Implement `update` method.")

    def render(self, surface: Surface) -> None:
        raise NotImplementedError("Implement `render` method.")

    def get_state(self) -> GameState:
        raise NotImplementedError("Implement `get_state` method.")


class PlayGameState(GameState):
    def __init__(self, screen: Rect):
        map: Map = TiledParser("resources/deck01.json").get_map()
        self.deck: DeckOfCards = DeckOfCards()
        self.deck.build()
        self.cpu = Cpu(map.get_object_group('CPU'))
        self.table = Table(map.get_object_group('TABLE'))
        self.actor = Player(map.get_object_group('PLAYER'))
        self.deck.deal(self.actor, self.cpu)
        self.deck.initial_deal(self.table)
        self.view = PlayGameView(map, self.actor, self.cpu, self.table)
        self.initial = True
        self.timer = Timer(1000)

    def update(self, time: int, event: Event) -> None:
        self.actor.update(time, event)
        if self.cpu.played() or self.initial is True:
            self.actor.play(self.table)
            if self.actor.played():
                self.timer = Timer(1000)
                self.cpu.turn()
                self.initial = False
        self.table.update(time)
        self.cpu.update(time, event)
        if self.actor.played():
            if self.timer.completed(time):
                self.cpu.play(self.table)
                if self.cpu.played():
                    self.actor.turn()
        self.table.update(time)

    def render(self, surface: Surface) -> None:
        """ Render debug info """
        self.view.blit_debug()
        self.view.render(surface)

    def get_state(self) -> GameState:
        return self

    def toggle_debug(self) -> None:
        self.view.toggle_debug()

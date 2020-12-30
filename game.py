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
        self.__debug = False
        self.state = StartGameState()
        self.mouse_event = None

    def update(self, time: int) -> None:
        """ Get the next state of the game """
        self.state = self.state.get_state()
        """ Update the state of sprites, level, etc """
        self.state.update(time, self.mouse_event)
        self.mouse_event = None

    def on_mouse_up(self, event: Event) -> None:
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
    def __init__(self, actor: Player, cpu: Player, table: Table):
        self.actor: Player = actor
        self.cpu: Player = cpu
        self.table: Table = table
        self.timer = Timer(1000)
        self.state = None

    def update(self, time: int, event: Event) -> None:
        if self.actor.cards_on_hand() == 0 and self.cpu.cards_on_hand() == 0:
            if self.table.deck.is_empty() and self.table.is_empty():
                self.state = EndGameState(self.actor, self.cpu, self.table)
                return
            if self.table.deck.is_empty() and not self.table.is_empty():
                self.table.plr_collect_last_cards()
                self.state = CollectWinningsState(self.actor, self.cpu, self.table)
                return
            self.state = DealCardsState(self.actor, self.cpu, self.table)
            return
        self.actor.update(time, event)
        self.actor.play(self.table)
        if self.actor.played():
            self.cpu.turn()
        self.table.update(time, self.actor)
        if self.table.has_winner():
            self.state = CollectWinningsState(self.actor, self.cpu, self.table)
            return
        if self.actor.played() and self.timer.looped(time):
            self.cpu.play(self.table)
            if self.cpu.played():
                self.actor.turn()
        self.table.update(time, self.cpu)
        if self.table.has_winner():
            self.state = CollectWinningsState(self.actor, self.cpu, self.table)
            return

    def render(self, surface: Surface) -> None:
        surface.fill((0, 38, 0))
        self.actor.draw(surface)
        self.cpu.draw(surface)
        self.table.draw(surface)

    def get_state(self) -> GameState:
        if self.state is not None:
            return self.state
        return self

    def toggle_debug(self) -> None:
        self.view.toggle_debug()


class StartGameState(GameState):
    def __init__(self):
        map: Map = TiledParser("resources/deck01.json").get_map()
        self.cpu = Cpu(map.get_object_group('CPU'))
        self.table = Table(map.get_object_group('TABLE'))
        self.actor = Player(map.get_object_group('PLAYER'))
        self.state = None
        self.actor.turn()

    def update(self, time: int, event: Event) -> None:
        if event is not None and self.table.table_deck.get_rect().colliderect(Rect(event.pos, (5, 5))):
            self.state = DealCardsState(self.actor, self.cpu, self.table)

    def render(self, surface: Surface) -> None:
        surface.fill((0, 38, 0))
        self.actor.draw(surface)
        self.cpu.draw(surface)
        self.table.draw(surface)

    def get_state(self) -> GameState:
        if self.state is not None:
            return self.state
        return self


class DealCardsState(GameState):
    def __init__(self, actor: Player, cpu: Player, table: Table):
        self.actor: Player = actor
        self.cpu: Player = cpu
        self.table: Table = table
        self.table.deck.start_deal()
        self.state = None

    def update(self, time: int, event: Event) -> None:
        if self.table.deck.is_finished() and \
                len(self.actor.win_cards) == 0 and len(self.cpu.win_cards) == 0:
            self.state = DealTableState(self.actor, self.cpu, self.table)
            return
        if self.table.deck.is_finished():
            self.state = PlayGameState(self.actor, self.cpu, self.table)
            return
        self.table.deck.deal(self.actor, self.cpu)

    def render(self, surface: Surface) -> None:
        surface.fill((0, 38, 0))
        self.actor.draw(surface)
        self.cpu.draw(surface)
        self.table.draw(surface)

    def get_state(self) -> GameState:
        if self.state is not None:
            return self.state
        return self


class DealTableState(GameState):
    def __init__(self, actor: Player, cpu: Player, table: Table):
        self.actor: Player = actor
        self.cpu: Player = cpu
        self.table: Table = table
        self.table.deck.start_deal()
        self.state = None

    def update(self, time: int, event: Event) -> None:
        if self.table.deck.is_finished():
            self.state = PlayGameState(self.actor, self.cpu, self.table)
            return
        self.table.deck.initial_deal(self.table)

    def render(self, surface: Surface) -> None:
        surface.fill((0, 38, 0))
        self.actor.draw(surface)
        self.cpu.draw(surface)
        self.table.draw(surface)

    def get_state(self) -> GameState:
        if self.state is not None:
            return self.state
        return self


class CollectWinningsState(GameState):
    def __init__(self, actor: Player, cpu: Player, table: Table, last: bool = False):
        self.actor: Player = actor
        self.cpu: Player = cpu
        self.table: Table = table
        self.last: bool = last
        self.state = None

    def update(self, time: int, event: Event) -> None:
        if self.table.has_winner() is False:
            if self.last is True:
                self.state = EndGameState(self.actor, self.cpu, self.table)
                return
            self.state = PlayGameState(self.actor, self.cpu, self.table)
            return
        self.table.collect_winnings()

    def render(self, surface: Surface) -> None:
        surface.fill((0, 38, 0))
        self.actor.draw(surface)
        self.cpu.draw(surface)
        self.table.draw(surface)

    def get_state(self) -> GameState:
        if self.state is not None:
            return self.state
        return self


class EndGameState(GameState):
    def __init__(self, actor: Player, cpu: Player, table: Table):
        self.actor: Player = actor
        self.cpu: Player = cpu
        self.table: Table = table
        self.state = None

    def update(self, time: int, event: Event) -> None:
        pass

    def render(self, surface: Surface) -> None:
        surface.fill((0, 38, 0))
        self.actor.draw(surface)
        self.cpu.draw(surface)
        self.table.draw(surface)

    def get_state(self) -> GameState:
        if self.state is not None:
            return self.state
        return self

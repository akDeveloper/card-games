from __future__ import annotations
from pygame import Rect, Surface, mouse, SYSTEM_CURSOR_ARROW, SYSTEM_CURSOR_HAND
from graphics import Graphics
from cards import Player, Table, Cpu
from tiled_parser import TiledParser, Map
from pygame.event import Event
from pygame.cursors import Cursor


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
        self.mouse_up_event = None
        self.mouse_pos: tuple = (0, 0)

    def update(self, time: int) -> None:
        """ Get the next state of the game """
        self.state = self.state.get_state()
        """ Update the state of sprites, level, etc """
        self.state.update(time, self.mouse_up_event, self.mouse_pos)
        self.mouse_up_event = None

    def on_mouse_up(self, event: Event) -> None:
        self.mouse_up_event = event

    def on_mouse_move(self, event: Event) -> None:
        self.mouse_pos = event.pos

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

    def update(self, time: int, mouse_up_event: Event, mouse_pos: tuple) -> None:
        if self.actor.cards_on_hand() == 0 and self.cpu.cards_on_hand() == 0 and \
                self.table.last_card_dealed():
            if self.table.deck.is_empty() and self.table.is_empty():
                self.state = EndGameState(self.actor, self.cpu, self.table)
                return
            if self.table.deck.is_empty() and not self.table.is_empty():
                self.table.plr_collect_last_cards()
                self.state = CollectWinningsState(self.actor, self.cpu, self.table)
                return
            self.state = DealCardsState(self.actor, self.cpu, self.table)
            return
        self.actor.update(time, mouse_up_event)
        self.actor.play(time, self.table)
        if self.actor.played():
            self.cpu.turn()
        self.table.update(time, self.actor)
        if self.table.has_winner():
            self.state = CollectWinningsState(self.actor, self.cpu, self.table)
            return
        if self.actor.played():
            self.cpu.play(time, self.table)
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

    def update(self, time: int, mouse_up_event: Event, mouse_pos: tuple) -> None:
        self.update_mouse_cursor(self.table.table_deck.get_rect(), mouse_pos)
        if mouse_up_event is not None and \
                self.table.table_deck.get_rect().colliderect(Rect(mouse_up_event.pos, (5, 5))):
            self.state = DealCardsState(self.actor, self.cpu, self.table, True)

    def render(self, surface: Surface) -> None:
        surface.fill((0, 38, 0))
        self.actor.draw(surface)
        self.cpu.draw(surface)
        self.table.draw(surface)

    def get_state(self) -> GameState:
        if self.state is not None:
            return self.state
        return self

    def update_mouse_cursor(self, src: Rect, mouse_pos: tuple) -> None:
        if src.colliderect(Rect(mouse_pos, (5, 5))) and \
                mouse.get_cursor() is not Cursor(SYSTEM_CURSOR_HAND):
            mouse.set_cursor(Cursor(SYSTEM_CURSOR_HAND))
        else:
            mouse.set_cursor(Cursor(SYSTEM_CURSOR_ARROW))


class DealCardsState(GameState):
    def __init__(self, actor: Player, cpu: Player, table: Table, initial: bool = False):
        self.actor: Player = actor
        self.cpu: Player = cpu
        self.table: Table = table
        self.table.deck.start_deal()
        self.state = None
        self.initial = initial
        mouse.set_cursor(Cursor(SYSTEM_CURSOR_ARROW))

    def update(self, time: int, mouse_up_event: Event, mouse_pos: tuple) -> None:
        if self.table.deck.is_finished() and self.initial is True:
            self.state = DealTableState(self.actor, self.cpu, self.table)
            return
        if self.table.deck.is_finished():
            self.state = PlayGameState(self.actor, self.cpu, self.table)
            return
        self.table.deck.deal(time, self.actor, self.cpu)

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

    def update(self, time: int, mouse_up_event: Event, mouse_pos: tuple) -> None:
        if self.table.deck.is_finished():
            self.state = PlayGameState(self.actor, self.cpu, self.table)
            return
        self.table.deck.initial_deal(time, self.table)

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

    def update(self, time: int, mouse_up_event: Event, mouse_pos: tuple) -> None:
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

    def update(self, time: int, mouse_up_event: Event, mouse_pos: tuple) -> None:
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

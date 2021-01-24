from graphics import ImageFactory, SpriteSheet
from pygame import Surface, Rect
from pygame.math import Vector2
from pygame.event import Event
from pygame.sprite import Sprite, Group
from tiled_parser import ObjectGroup
import random
from math import ceil


def bresenham(x0, y0, x1, y1):
    """
    https://github.com/encukou/bresenham/blob/master/bresenham.py
    Yield integer coordinates on the line from (x0, y0) to (x1, y1).
    Input coordinates should be integers.
    The result will contain both the start and the end point.
    """
    dx = x1 - x0
    dy = y1 - y0

    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1

    dx = abs(dx)
    dy = abs(dy)

    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0

    D = 2 * dy - dx
    y = 0

    for x in range(dx + 1):
        yield x0 + x * xx + y * yx, y0 + x * xy + y * yy
        if D >= 0:
            y += 1
            D -= 2 * dx
        D += 2 * dy


class Steer(object):
    def __init__(self, pos: tuple):
        self.desired = None
        self.max_speed = 5
        self.max_force = 0.7
        self.approach_radius = 30
        self.pos = Vector2(pos[0], pos[1])
        self.vel = Vector2(self.max_speed, 0).rotate(random.uniform(0, 360))
        self.acc = Vector2(0, 0)
        self.dist = 0

    def seek_with_approach(self, target: tuple):
        self.desired = (target - self.pos)
        dist = self.desired.length()
        self.desired.normalize_ip()
        if dist < self.approach_radius:
            self.desired *= dist / self.approach_radius * self.max_speed
        else:
            self.desired *= self.max_speed
        steer = (self.desired - self.vel)
        if steer.length() > self.max_force:
            steer.scale_to_length(self.max_force)
        self.dist = dist
        return steer

    def update(self, target: tuple):
        self.acc = self.seek_with_approach(target)
        # equations of motion
        self.vel += self.acc
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)
        self.pos += self.vel


class CardsImageFactory(ImageFactory):
    FILENAME = "resources/win-cards.png"
    """
    sprite: 71 x 96
    """
    def __init__(self):
        self.sheet = SpriteSheet(self.FILENAME, (0, 38, 0))
        self.images = []
        self.create()

    def create(self) -> None:
        width = 71
        height = 96
        for y in range(5):
            for x in range(13):
                self.images.append(
                    self.sheet.get_image(
                        x * width,
                        y * height,
                        width,
                        height
                    )
                )

    def get_image(self, index: int) -> Surface:
        return self.images[index]


class Card(Sprite):
    def __init__(self, face: str, suite: str, image: Surface, back: Surface):
        super().__init__()
        self.face: str = face
        self.suite: str = suite
        self.face_image = image
        self.image = back
        self.rect = image.get_rect()
        self.back = back
        self.path: list = []
        self.steer = None
        self.target = None

    def move_to(self, target: tuple) -> None:
        self.target = target

    def is_dealed(self) -> bool:
        return self.rect.topleft == self.target

    def update(self, time: int):
        if self.target is not None:
            dx = self.target[0] - self.rect.left
            new_x = dx * 0.3
            if abs(new_x) > 0 and abs(new_x) < 1:
                new_x = -1 if new_x < 0 else 1
            self.rect.left += new_x
            dy = self.target[1] - self.rect.top
            new_y = dy * 0.3
            if abs(new_y) > 0 and abs(new_y) < 1:
                new_y = -1 if new_y < 0 else 1
            self.rect.top += new_y

    def flip(self) -> None:
        self.image = self.back

    def show(self) -> None:
        self.image = self.face_image


class Table(object):
    def __init__(self, objectgroup: ObjectGroup):
        self.objectgroup = objectgroup
        self.cards: Group = Group()
        self.deck: DeckOfCards = DeckOfCards()
        self.table_deck = self.objectgroup.get_item("table_deck")
        self.deck.build(self.table_deck.get_rect().topleft)
        self.current_card: int = 0
        self.__last_card: Card = None
        self.__compare_cards: list = []
        self.__winning_player: Player = None
        self.__last_winner: Player = None
        self.__is_bonus_win = False

    def deal(self, actor: 'Player', cpu: 'Player') -> None:
        self.deck.deal(actor, cpu)

    def initial_deal(self) -> None:
        self.deck.initial_deal(self)

    def has_winner(self) -> bool:
        return self.__winning_player is not None

    def add_card(self, card: Card) -> None:
        item = self.objectgroup.get_item('table')
        card.rect.topleft = (item.get_rect().left + (self.get_cards() * 20), item.get_rect().top)
        self.cards.add(card)
        self.__last_card = card

    def place_card(self, card: Card) -> None:
        item = self.objectgroup.get_item('table')
        card.rect.topleft = item.get_rect().topleft
        self.cards.add(card)
        self.__compare_cards = [self.__last_card, card]
        self.__last_card = card
        card.show()

    def get_cards(self) -> int:
        return len(self.cards.sprites())

    def is_empty(self) -> bool:
        return len(self.cards.sprites()) == 0

    def get_last_card(self) -> Card:
        return self.__last_card

    def update(self, time: int, plr: 'Player') -> None:
        if self.check_for_win():
            self.__winning_player = plr

    def plr_collect_last_cards(self) -> None:
        self.__winning_player = self.__last_winner

    def collect_winnings(self) -> None:
        if len(self.cards.sprites()) == 0:
            self.__last_winner = self.__winning_player
            self.__winning_player = None
            self.__last_card = None
            self.__compare_cards = []
            return
        if self.__is_bonus_win is True:
            """ Bonus"""
            card = self.cards.sprites()[0]
            self.__winning_player.put_on_bonus(card)
            self.cards.remove(card)
            self.__is_bonus_win = False
            return
        card = self.cards.sprites()[0]
        self.__winning_player.put_on_deck(card)
        self.cards.remove(card)

    def draw(self, surface: Surface):
        self.cards.draw(surface)
        self.deck.draw(surface)

    def check_for_win(self) -> bool:
        if len(self.__compare_cards) != 2:
            return False
        result: bool = False
        pre: Card = self.__compare_cards[0]
        last: Card = self.__compare_cards[1]
        if pre is None or last is None:
            return False
        if pre.face == last.face or last.face == "Jack":
            result = True
            if len(self.cards.sprites()) == 2 and pre.face == last.face:
                self.__is_bonus_win = True
        self.__compare_cards = []
        return result


class Player(object):
    def __init__(self, objectgroup: ObjectGroup):
        self.on_hand: Group = Group()
        self.current_deck_index: int = 0
        self.card_to_play: Card = None
        self.objectgroup = objectgroup
        self.win_cards: Group = Group()
        self.bonus_cards: Group = Group()
        self.__played = False
        self.__turn = False

    def played(self) -> bool:
        return self.__played

    def turn(self) -> None:
        self.__turn = True
        self.__played = False

    def is_turn(self) -> bool:
        return self.__turn

    def update(self, time: int, mouse_event: Event) -> None:
        if mouse_event is None:
            return
        for s in self.on_hand.sprites():
            if s.rect.colliderect(Rect(mouse_event.pos, (5, 5))):
                self.card_to_play = s
                return

    def draw(self, surface: Surface):
        self.on_hand.draw(surface)
        if len(self.bonus_cards.sprites()) > 0:
            copy = self.bonus_cards.sprites()
            copy.reverse()
            for s in copy:
                surface.blit(s.image, s.rect)
        if len(self.win_cards.sprites()) > 0:
            self.win_cards.draw(surface)

    def take_card(self, card: Card) -> tuple:
        index = self.cards_on_hand()
        item = self.objectgroup.get_items()[index]
        # card.rect.topleft = item.get_rect().topleft
        # self.on_hand.add(card)
        card.show()
        return item.get_rect().topleft

    def cards_on_hand(self) -> int:
        return len(self.on_hand.sprites())

    def play(self, table: Table) -> None:
        if self.card_to_play is None:
            return
        if self.__turn is False:
            return
        table.place_card(self.card_to_play)
        self.on_hand.remove(self.card_to_play)
        self.card_to_play = None
        self.__played = True
        self.__turn = False

    def put_on_deck(self, card: Card) -> None:
        card.rect.topleft = self.objectgroup.get_item("deck").get_rect().topleft
        self.win_cards.add(card)
        card.flip()

    def put_on_bonus(self, card: Card) -> None:
        bonus_cards = len(self.bonus_cards.sprites()) + 1
        card.rect.topleft = self.objectgroup.get_item("deck").get_rect().topleft
        card.rect.left += (bonus_cards * 20)
        self.bonus_cards.add(card)
        self.bonus_cards.sprites().reverse()


class Cpu(Player):
    def take_card(self, card: Card) -> None:
        pos = super().take_card(card)
        card.flip()
        return pos

    def play(self, table: Table) -> None:
        last = table.get_last_card()
        for c in self.on_hand:
            if last is None:
                self.card_to_play = c
                break
            if c.face == last.face or c.face == "Jack":
                self.card_to_play = c
                break
        if self.card_to_play is None:
            self.card_to_play = self.on_hand.sprites()[0]
        super().play(table)


class DeckOfCards(object):
    NUMBER_OF_CARDS = 52

    def __init__(self):
        self.__factory = CardsImageFactory()
        self.__deck: list = []
        self.__sprites: Group = Group()
        self.__deal_finished = False
        self.__dealing_card = None

    def build(self, topleft: tuple) -> None:
        face: list = ["Ace", "Deuce", "Three", "Four", "Five",
                      "Six", "Seven", "Eight", "Nine", "Ten", "Jack", "Queen", "King"]
        suite: list = ["Spades", "Hearts", "Clubs", "Diamonds"]
        back: Surface = self.__factory.get_image(52)
        for i in range(self.NUMBER_OF_CARDS):
            f = int(i % 13)
            s = int(i / 13)
            card = Card(face[f], suite[s], self.__factory.get_image(i), back)
            card.rect.topleft = topleft
            self.__deck.append(card)
        random.shuffle(self.__deck)
        for c in self.__deck:
            self.__sprites.add(c)

    def draw(self, surface: Surface) -> None:
        self.__sprites.draw(surface)

    def start_deal(self):
        self.__deal_finished = False

    def is_finished(self) -> bool:
        return self.__deal_finished

    def is_empty(self) -> bool:
        return len(self.__deck) == 0

    def initial_deal(self, table: Table) -> None:
        if table.get_cards() == 4:
            self.__deal_finished = True
            return
        card = self.__deck.pop()
        table.add_card(card)
        card.show()
        self.__sprites.remove(card)

    def deal(self, time: int, actor: Player, cpu: Player) -> None:
        if actor.cards_on_hand() == 6 and cpu.cards_on_hand() == 6:
            self.__deal_finished = True
            return
        """ Deal to actor """
        if actor.cards_on_hand() < 6:
            if self.__dealing_card is None:
                self.__dealing_card = self.__deck.pop()
                target = actor.take_card(self.__dealing_card)
                self.__dealing_card.move_to(target)
            self.__dealing_card.update(time)
            if self.__dealing_card.is_dealed():
                actor.on_hand.add(self.__dealing_card)
                self.__sprites.remove(self.__dealing_card)
                self.__dealing_card.target = None
                self.__dealing_card = None
        """ Deal to cpu """
        if actor.cards_on_hand() == 6:
            if self.__dealing_card is None:
                self.__dealing_card = self.__deck.pop()
                target = cpu.take_card(self.__dealing_card)
                self.__dealing_card.move_to(target)
            self.__dealing_card.update(time)
            if self.__dealing_card.is_dealed():
                cpu.on_hand.add(self.__dealing_card)
                self.__sprites.remove(self.__dealing_card)
                self.__dealing_card.target = None
                self.__dealing_card = None
        # card = self.__deck.pop()
        # cpu.take_card(card)
        # self.__sprites.remove(card)

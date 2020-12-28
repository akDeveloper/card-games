from graphics import ImageFactory, SpriteSheet
from pygame import Surface, Rect
from pygame.event import Event
from pygame.sprite import Sprite, Group
from tiled_parser import ObjectGroup
import random


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
        face: str = face
        suite: str = suite
        self.image = image
        self.rect = image.get_rect()
        self.back = back

    def update(self, time: int):
        pass

class Table(object):
    def __init__(self, pos: ObjectGroup):
        self.cards: Group = Group()
        self.current_card: int = 0
        self.objectgroup = pos

    def add_card(self, card: Card) -> None:
        item = self.objectgroup.get_items()[0]
        card.rect.topleft = (item.get_rect().left + (self.get_cards() * 50), item.get_rect().top)
        self.cards.add(card)

    def place_card(self, card: Card) -> None:
        item = self.objectgroup.get_items()[0]
        card.rect.topright = (item.get_rect().topright)
        self.cards.add(card)

    def get_cards(self) -> int:
        return len(self.cards.sprites())

    def update(self, time: int) -> None:
        pass

    def draw(self, surface: Surface):
        self.cards.draw(surface)

class Player(object):
    def __init__(self, pos: ObjectGroup):
        self.on_hand: Group = Group()
        self.current_deck_index: int = 0
        self.card_to_play: Card = None
        self.objectgroup = pos
        self.__played = False
        self.__turn = False

    def played(self) -> bool:
        return self.__played

    def turn(self) -> None:
        self.__turn = True
        self.__played = False

    def update(self, time: int, mouse_event: Event) -> None:
        if mouse_event is None:
            return
        for s in self.on_hand.sprites():
            if s.rect.colliderect(Rect(mouse_event.pos, (5, 5))):
                self.card_to_play = s
                return

    def draw(self, surface: Surface):
        self.on_hand.draw(surface)

    def take_card(self, card: Card) -> None:
        index = self.cards_on_hand()
        item = self.objectgroup.get_items()[index]
        card.rect.topleft = item.get_rect().topleft
        self.on_hand.add(card)

    def cards_on_hand(self) -> int:
        return len(self.on_hand.sprites())

    def play(self, table: Table) -> None:
        if self.card_to_play is None:
            return
        table.place_card(self.card_to_play)
        self.on_hand.remove(self.card_to_play)
        self.card_to_play = None
        self.__played = True
        self.__turn = False


class Cpu(Player):
    def play(self, table: Table) -> None:
        self.card_to_play = self.on_hand.sprites()[0]
        super().play(table)


class DeckOfCards(object):
    NUMBER_OF_CARDS = 52

    def __init__(self):
        self.__factory = CardsImageFactory()
        self.__deck: list = []

    def build(self) -> None:
        face: list = ["Ace", "Deuce", "Three", "Four", "Five",
                      "Six", "Seven", "Eight", "Nine", "Ten", "Jack", "Queen", "King"]
        suite: list = ["Spades", "Hearts", "Clubs", "Diamonds"]
        back: Surface = self.__factory.get_image(54)
        for i in range(self.NUMBER_OF_CARDS):
            f = int(i % 13)
            s = int(i / 13)
            self.__deck.append(Card(face[f], suite[s], self.__factory.get_image(i), back))
        random.shuffle(self.__deck)

    def get_card(self, index: int) -> Sprite:
        return self.__deck[index]

    def initial_deal(self, table: Table) -> None:
        for i in range(4):
            table.add_card(self.__deck.pop())

    def deal(self, pl1: Player, pl2: Player) -> None:
        for i in range(6):
            pl1.take_card(self.__deck.pop())
            pl2.take_card(self.__deck.pop())

from pygame import Surface, Rect, image
from pygame.sprite import Sprite
from pygame.transform import scale2x
from pygame.display import set_mode, update
from pygame.locals import HWSURFACE, SRCALPHA, FULLSCREEN


class Graphics(object):
    def __init__(self, width: int, height: int):
        self.screen = set_mode((width, height))
        """ temp Surface for handling the small graphics """
        self.__surface = Surface((width, height))

    def get_surface(self) -> Surface:
        return self.__surface

    def render(self) -> None:
        self.__surface.convert_alpha()
        self.screen.blit(self.__surface, (0, 0))
        update()


class SpriteSheet(object):

    def __init__(self, filename, colorkey: tuple):
        self.sprite_sheet = image.load(filename)
        self.colorkey = colorkey

    def get_image(self, x: int, y: int, width: int, height: int) -> Surface:
        image = Surface([width, height], SRCALPHA).convert()
        image.set_colorkey(self.colorkey)
        image.blit(self.sprite_sheet, (0, 0), (x, y, width, height))
        return image


class ImageFactory(object):
    """
    Loads images from a Spritesheet and index them.
    Deliver the image Surface for the given index.
    """
    def __init__(self):
        raise RuntimeError("Can not instatiate")

    def get_image(self, index: int) -> Surface:
        raise NotImplementedError("Implement `get_image` method.")

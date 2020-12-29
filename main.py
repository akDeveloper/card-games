import pygame
from pygame.locals import K_ESCAPE, QUIT, KEYUP, KEYDOWN, K_d, MOUSEMOTION, MOUSEBUTTONUP
from pygame.event import Event
from game import Game


class App(object):
    FPS = 20

    def __init__(self):
        self.running = True

    def on_init(self) -> None:
        pygame.init()
        self.game = Game()

    def on_loop(self, time: int) -> None:
        self.game.update(time)

    def on_render(self) -> None:
        self.game.render()

    def on_exit(self) -> None:
        self.running = False

    def on_cleanup(self):
        pygame.quit()

    def on_key_down(self, event: Event):
        pass

    def on_mouse_move(self, event: Event):
        pass  # print(event.pos)

    def on_mouse_up(self, event: Event):
        self.game.on_mouse_up(event)

    def on_key_up(self, event: Event):
        if event.key == K_ESCAPE:
            self.running = False
        if event.key == K_d:
            self.game.toggle_debug()

    def on_event(self, event: Event) -> None:
        if event.type == QUIT:
            self.on_exit()
        elif event.type == KEYUP:
            self.on_key_up(event)
        elif event.type == KEYDOWN:
            self.on_key_down(event)
        elif event.type == MOUSEMOTION:
            self.on_mouse_move(event)
        elif event.type == MOUSEBUTTONUP:
            self.on_mouse_up(event)

    def on_execute(self):
        if self.on_init() is False:
            return

        clock = pygame.time.Clock()

        while(self.running):
            clock.tick(self.FPS)
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop(clock.get_time())
            self.on_render()
        self.on_cleanup()


if __name__ == "__main__":
    app = App()
    app.on_execute()

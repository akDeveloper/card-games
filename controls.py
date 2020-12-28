from enum import Enum
import pygame
from pygame.event import Event
from typing import Optional
from pygame.joystick import Joystick, get_count
from pygame.locals import K_LEFT, K_RIGHT, K_UP, K_DOWN, \
    K_a, K_s, K_d, K_z, K_x, K_c, K_RETURN


class State(Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'
    UPLEFT = 'upleft'
    UPRIGHT = 'upright'
    DOWNLEFT = 'downleft'
    DOWNRIGHT = 'downright'
    X = 'X'
    Y = 'Y'
    A = 'A'
    B = 'B'
    R = 'R'
    L = 'L'
    START = 'start'
    SELECT = 'select'
    IDLE = 'idle'


class Direction(object):

    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def get_active(self) -> Optional[str]:
        for state, value in self.__states().items():
            if value is True:
                return state

    def get(self, state: str) -> bool:
        '''
        Get the status of a state
        '''
        states = self.__states()
        if state in states:
            return states.get(state)
        return False

    def is_idle(self) -> bool:
        return self.x == 0 and self.y == 0

    def __states(self):
        return {
            State.IDLE: self.x == 0 and self.y == 0,
            State.UPLEFT: self.y == 1 and self.x == -1,
            State.UPRIGHT: self.y == 1 and self.x == 1,
            State.DOWNLEFT: self.y == -1 and self.x == -1,
            State.DOWNRIGHT: self.y == -1 and self.x == 1,
            State.UP: self.y == 1 and self.x == 0,
            State.DOWN: self.y == -1 and self.x == 0,
            State.LEFT: self.x == -1 and self.y == 0,
            State.RIGHT: self.x == 1 and self.y == 0,
        }


class Buttons(object):
    def __init__(self):
        self.states = {
            State.X: 0,
            State.Y: 0,
            State.A: 0,
            State.B: 0,
            State.R: 0,
            State.L: 0,
            State.START: 0,
            State.SELECT: 0
        }

    def reset(self) -> None:
        for item in self.states:
            self.states[item] = 0

    def get_pressed(self) -> Optional[str]:
        for state, value in self.states.items():
            if value == 1:
                return state

    def pressed(self, button: str) -> None:
        if button in self.states:
            self.states[button] = 1

    def released(self, button: str) -> None:
        if button in self.states:
            self.states[button] = 0

    def is_pressed(self, button: str) -> bool:
        if button in self.states:
            return self.states[button] == 1
        return False

    def is_released(self, button: str) -> bool:
        if button in self.states:
            return self.states[button] == 0
        return False


class UserInput(object):
    def __init__(self, direction: Direction, button: Buttons):
        self.direction = direction
        self.button = button

class AiInput(UserInput):
    def __init__(self):
        self.direction = Direction()
        self.button = Buttons()

class Input(object):
    def __init__(self):
        raise RuntimeError("Can not instatiate")

    def key_down(self, e: Event) -> None:
        raise NotImplementedError("Implement `key_down` method.")

    def key_up(self, e: Event) -> None:
        raise NotImplementedError("Implement `key_up` method.")

    def on_event(self) -> None:
        raise NotImplementedError("Implement `on_event` method.")

    def get_direction(self) -> Direction:
        raise NotImplementedError("Implement `get_direction` method.")

    def get_buttons(self) -> Buttons:
        raise NotImplementedError("Implement `get_buttons` method.")

    def get_user_input(self) -> UserInput:
        raise NotImplementedError("Implement `get_user_input` method.")


class Joypad(Input):
    def __init__(self):
        self.joystick = None
        self.joystick_name = None
        self.hats = []
        self.direction = Direction()
        self.buttons = Buttons()
        self.button_maps = {
            0: State.X,
            1: State.A,
            2: State.B,
            3: State.Y,
            4: State.L,
            5: State.R,
            8: State.SELECT,
            9: State.START
        }
        if get_count() > 0:
            joystick = Joystick(0)
            joystick.init()
            self.joystick = joystick
            self.joystick_name = joystick.get_name()
            self.hats = joystick.get_numhats()
            self.axis = joystick.get_numaxes()

    def key_down(self, e: Event) -> None:
        pass

    def key_up(self, e: Event) -> None:
        pass

    def on_event(self) -> None:
        x = y = 0
        for i in range(self.hats):
            hat = self.joystick.get_hat(i)
            x = hat[0]
            y = hat[1]

        if self.direction.is_idle():
            jx = self.joystick.get_axis(0)
            jy = self.joystick.get_axis(1)
            x = int(jx)
            y = int(round(jy, 0)) * -1

        self.direction.update(x, y)
        buttons = self.joystick.get_numbuttons()
        for b in range(buttons):
            button = self.joystick.get_button(b)
            if button == 1:
                self.buttons.pressed(self.button_maps.get(b))
            else:
                self.buttons.released(self.button_maps.get(b))

    def get_direction(self) -> Direction:
        return self.direction

    def get_buttons(self) -> Buttons:
        return self.buttons

    def get_user_input(self) -> UserInput:
        return UserInput(self.direction, self.buttons)


class Keyboard(Input):

    def __init__(self):
        self.direction = Direction()
        self.buttons = Buttons()
        self.button_maps = {
            K_a: State.Y,
            K_s: State.X,
            K_d: State.L,
            K_z: State.B,
            K_x: State.A,
            K_c: State.R,
            K_RETURN: State.START
        }
        self.direction_maps = {
            K_UP: State.UP,
            K_DOWN: State.DOWN,
            K_LEFT: State.LEFT,
            K_RIGHT: State.RIGHT,
        }

    def key_down(self, e: Event) -> None:
        if e.key in self.button_maps:
            self.buttons.pressed(self.button_maps.get(e.key))

    def key_up(self, e: Event) -> None:
        if e.key in self.button_maps:
            self.buttons.released(self.button_maps.get(e.key))

    def on_event(self) -> None:
        pressed = pygame.key.get_pressed()
        x = y = 0

        if pressed[K_RIGHT] == 1:
            x = 1
        if pressed[K_LEFT] == 1:
            x = -1
        if pressed[K_UP] == 1:
            y = 1
        if pressed[K_DOWN] == 1:
            y = -1
        if pressed[K_RIGHT] == 0 and pressed[K_LEFT] == 0:
            x = 0
        if pressed[K_UP] == 0 and pressed[K_DOWN] == 0:
            y = 0

        self.direction.update(x, y)

    def get_direction(self) -> Direction:
        return self.direction

    def get_buttons(self) -> Buttons:
        return self.buttons

    def get_user_input(self) -> UserInput:
        return UserInput(self.direction, self.buttons)


class Controller(Input):

    def __init__(self):
        keyboard = Keyboard()
        joypad = Joypad()
        if joypad.joystick is None:
            joypad = None
        self.input = joypad or keyboard

    def key_down(self, e: Event) -> None:
        self.input.key_down(e)

    def key_up(self, e: Event) -> None:
        self.input.key_up(e)

    def on_event(self) -> None:
        self.input.on_event()

    def get_direction(self) -> Direction:
        return self.input.get_direction()

    def get_buttons(self) -> Buttons:
        return self.input.get_buttons()

    def get_user_input(self) -> UserInput:
        return UserInput(self.get_direction(), self.get_buttons())

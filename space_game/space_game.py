import asyncio
import curses
from collections import defaultdict
import itertools
from pathlib import Path
import random
import time
from typing import Dict, List, NoReturn, Optional, Tuple, Union

from space_game.physics import update_speed
from space_game.settings import MapSettings, ContolSettings, TIC_TIMEOUT


class Frame:
    def __init__(self,
                 content: str,
                 name: Optional[str] = ''
                 ):
        self.content = content
        self.name = name
        self.height, self.width = get_frame_size(self.content)

    def __str__(self) -> str:
        return f'{Frame.__name__}(name={self.name})'

    __repr__ = __str__


class MapObject:
    """
    This class represents a position of an object on the map
    """

    def __init__(self,
                 frame: Frame,
                 start_x: Union[float, int],
                 start_y: Union[float, int]
                 ):
        self.frame = frame
        self.x = start_x
        self.y = start_y
        self.start_x = start_x
        self.start_y = start_y

    def __str__(self) -> str:
        return f'{MapObject.__name__}(' \
               f'frame={self.frame}, ' \
               f'current_x={self.x}, ' \
               f'current_y={self.y}, ' \
               f'start_x={self.start_x}, ' \
               f'start_y={self.start_y})'

    __repr__ = __str__

    def current_coordinates(self) -> Tuple[int, int]:
        return self.x, self.y

    def change_coordinates(self,
                           x: Union[float, int],
                           y: Union[float, int]) -> NoReturn:
        self.x = x
        self.y = y

    def change_frame(self, frame: Frame) -> NoReturn:
        self.frame = frame

    def intersect(self, other: 'MapObject') -> bool:
        """
        Check that this object and another are intersected by
        framing rectangles.
        :param other:
        :return: True if there is intersection and False otherwise
        """

        x_bottom, y_bottom = self.x, self.y
        x_top = self.x + self.frame.width
        y_top = self.y + self.frame.height

        x_bottom_other, y_bottom_other = other.current_coordinates()
        x_top_other = x_bottom_other + other.frame.width
        y_top_other = y_bottom_other + other.frame.height

        if x_bottom <= x_bottom_other <= x_top:
            if y_bottom <= y_bottom_other <= y_top:
                return True
            elif y_bottom <= y_top_other <= y_top:
                return True
            else:
                return False
        elif x_bottom <= x_top_other <= x_top:
            if y_bottom <= y_bottom_other <= y_top:
                return True
            elif y_bottom <= y_top_other <= y_top:
                return True
            else:
                return False

        return False


class SpaceGame:
    def __init__(self):
        self._coroutines = []
        self._all_frames = read_objects(Path.cwd() / 'frames')
        self._dynamic_objects = {}

        self._canvas = None

    def run(self) -> NoReturn:
        assert MapSettings.STAR_COEFF > 0

        curses.update_lines_cols()
        curses.wrapper(self._run_event_loop)

    def _run_event_loop(self, canvas) -> NoReturn:
        curses.curs_set(False)
        self._canvas = canvas

        self._canvas.border()
        self._canvas.nodelay(True)

        max_y, max_x = self._canvas.getmaxyx()
        # Compute correct window sizes without border lines
        max_y -= 2
        max_x -= 2

        n_stars = int((max_y*max_x) * MapSettings.STAR_COEFF)
        coordinates = {(random.randint(1, max_x), random.randint(1, max_y))
                       for _ in range(0, n_stars)}
        self._coroutines = [
            self.blink(MapObject(
                frame=Frame(random.choice(MapSettings.STAR_SET)),
                start_x=x,
                start_y=y)
            )
            for i, (x, y) in enumerate(coordinates)
        ]
        self._coroutines.append(self.animate_spaceship(start_y=10, start_x=10))
        self._coroutines.append(self.fill_orbit_with_garbage())

        while True:
            for coroutine in self._coroutines.copy():
                try:
                    coroutine.send(None)
                    self._canvas.refresh()
                except StopIteration:
                    self._coroutines.remove(coroutine)
            if not self._coroutines:
                break

            time.sleep(TIC_TIMEOUT)

    async def fire(self,
                   start_x: int,
                   start_y: int,
                   x_speed: Optional[Union[float, int]] = 0,
                   y_speed: Optional[Union[float, int]] = -0.3):
        """
        Display animation of gun shot, direction and speed
        can be specified.
        """

        x, y = start_x, start_y

        self._canvas.addstr(round(y), round(x), '*')
        await sleep(0)

        self._canvas.addstr(round(y), round(x), 'O')
        await sleep(0)
        self._canvas.addstr(round(y), round(x), ' ')

        x += x_speed
        y += y_speed

        symbol = '-' if x_speed else '|'

        max_y, max_x = self._canvas.getmaxyx()
        max_y, max_x = max_y - 1, max_x - 1

        curses.beep()
        fire_shot_object = MapObject(Frame(symbol), x, y)
        while 1 < y < max_y and 1 < x < max_x:
            self._canvas.addstr(round(y), round(x), symbol)
            await sleep(0)
            self._canvas.addstr(round(y), round(x), ' ')
            fire_shot_object.change_coordinates(x + x_speed, y + y_speed)
            for obj_id, obj in self._dynamic_objects.items():
                if (obj_id.startswith('rubbish')
                        and obj.intersect(fire_shot_object)):
                    draw_frame(self._canvas, obj.x, obj.y, obj.frame,
                               negative=True)
                    self._dynamic_objects.pop(obj_id)
                    await self.explode(obj.x, obj.y)
                    return

            y += y_speed
            x += x_speed

    async def animate_spaceship(self,
                                start_x: int,
                                start_y: int):
        """
        A coroutine for drawing and moving the spaceship.
        :param start_x: a start x (column) point for the spaceship
        :param start_y: a start y (row) point for the spaceship
        :return:
        """

        x_speed, y_speed = 0, 0
        max_y, max_x = self._canvas.getmaxyx()
        # Compute correct window sizes including borders
        max_x -= 1
        max_y -= 1

        spaceship_frames = self._all_frames['spaceship']
        spaceship = MapObject(
            frame=spaceship_frames['rocket_frame_1'],
            start_x=start_x,
            start_y=start_y
        )
        self._dynamic_objects['spaceship'] = spaceship

        for i in itertools.cycle([1, 2]):
            x, y = spaceship.current_coordinates()
            frame = spaceship_frames[f'rocket_frame_{i}']

            draw_frame(self._canvas, x, y, frame)
            for _ in range(0, 2):
                x_direction, y_direction, space_pressed = \
                    read_controls(self._canvas)
                x_speed, y_speed = update_speed(x_speed, y_speed, x_direction,
                                                y_direction)
                await sleep(1)
            draw_frame(self._canvas, x, y, frame, negative=True)

            if y + y_speed <= 1:
                y = 1
            elif y + y_speed + frame.height > max_y:
                y = max_y - frame.height
            else:
                y += y_speed

            if x + x_speed <= 1:
                x = 1
            elif x + x_speed + frame.width >= max_x:
                x = max_x - frame.width
            else:
                x += x_speed

            if space_pressed:
                x_fire = round(x + spaceship.frame.width // 2)
                self._coroutines.append(self.fire(x_fire, y))

            spaceship.change_frame(frame)
            spaceship.change_coordinates(x, y)

    async def blink(self, star: MapObject):
        """
        Draw a blinking symbol.
        """
        x, y = star.current_coordinates()
        symbol = star.frame.content
        while True:
            self._canvas.addstr(y, x, symbol, curses.A_DIM)
            await sleep(random.randint(1, 10))

            self._canvas.addstr(y, x, symbol)
            await sleep(random.randint(1, 10))

            self._canvas.addstr(y, x, symbol, curses.A_BOLD)
            await sleep(random.randint(1, 10))

            self._canvas.addstr(y, x, symbol)
            await sleep(random.randint(1, 10))

    async def fly_garbage(self,
                          rubbish_object: MapObject,
                          rubbish_id: str,
                          speed: Optional[float] = 0.5):
        """
        Animate garbage, flying from top to bottom.
        A start_x position will stay same, as specified on start.
        """

        max_y, max_x = self._canvas.getmaxyx()

        x, y = rubbish_object.current_coordinates()
        while y < max_y:
            if rubbish_id not in self._dynamic_objects:
                return
            rubbish_object.change_coordinates(x, y)
            draw_frame(self._canvas, x, y, rubbish_object.frame)
            await sleep(0)
            draw_frame(self._canvas, x, y, rubbish_object.frame, negative=True)
            y += speed

        self._dynamic_objects.pop(rubbish_id)

    async def fill_orbit_with_garbage(self):
        rubbish_frames = [
            frame
            for name, frame in self._all_frames['rubbish'].items()
            if not name.startswith('rocket')
        ]

        max_y, max_x = self._canvas.getmaxyx()
        max_frame_width = max([frame.width for frame in rubbish_frames])

        rubbish_count = 0
        while True:
            rubbish_coroutines = []
            right_border = max(2, max_x * MapSettings.RUBBISH_COEFF //
                               max_frame_width)
            n_spawned_objects = random.randint(1, int(right_border))
            next_object = False
            for _ in range(0, n_spawned_objects):
                frame = rubbish_frames[
                    random.randint(0, len(rubbish_frames) - 1)]
                start_x = random.randint(-frame.width + 2, max_x - 2)
                start_y = -frame.height
                rubbish_object = MapObject(frame, start_x, start_y)
                for existing_object in self._dynamic_objects.values():
                    if (rubbish_object.intersect(existing_object)
                            or existing_object.intersect(rubbish_object)):
                        next_object = True
                        break

                if next_object:
                    next_object = False
                    continue

                rubbish_id = f'rubbish_{rubbish_count}'
                if rubbish_count > 10000:
                    rubbish_count = 0
                else:
                    rubbish_count += 1

                self._dynamic_objects[rubbish_id] = rubbish_object
                rubbish_coroutines.append(self.fly_garbage(rubbish_object,
                                                           rubbish_id))

            if rubbish_coroutines:
                self._coroutines.extend(rubbish_coroutines)
            await sleep(5)

    async def explode(self, x, y):
        explosion_frames = self._all_frames['explosion']
        curses.beep()
        for frame in explosion_frames.values():
            draw_frame(self._canvas, x, y, frame)

            await asyncio.sleep(0)
            draw_frame(self._canvas, x, y, frame, negative=True)
            await asyncio.sleep(0)


def read_objects(path: Path) -> Dict[str, Dict[str, Frame]]:
    """
    Read objects the files and returns them in a string representation.
    :param path: a directory with objects.
    :return: A dict where a key is an object category and a value is a dict
        where a key is a file name without suffix and a value is
        a string representing the frame.
    """

    objects = defaultdict(dict)
    for dir_path in path.glob('*/*'):
        with open(dir_path, 'r') as file:
            objects[dir_path.parent.stem][dir_path.stem] = Frame(''.join(file),
                                                                 dir_path.stem)

    return objects


def read_controls(canvas) -> Tuple[int, int, bool]:
    """Read keys pressed and returns tuple with controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == ContolSettings.UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == ContolSettings.DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == ContolSettings.RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == ContolSettings.LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == ContolSettings.SPACE_KEY_CODE:
            space_pressed = True

    return columns_direction, rows_direction, space_pressed


def draw_frame(canvas,
               x: Union[float, int],
               y: Union[float, int],
               frame: Frame,
               negative: Optional[bool] = False):
    """
    Draw multiline text fragment on canvas,
    erase text instead of drawing if negative=True is specified.
    """

    max_y, max_x = canvas.getmaxyx()

    for row, line in enumerate(frame.content.splitlines(), round(y)):
        if row <= 0:
            continue

        if row >= max_y - 1:
            break

        for column, symbol in enumerate(line, round(x)):
            if column <= 0:
                continue

            if column >= max_x - 1:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner
            # of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == max_y - 1 and column == max_x - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(frame: str) -> Tuple[int, int]:
    """
    Calculate size of multiline text fragment, return pair — number
    of rows and columns.
    :returns: a row and a column sizes
    """

    lines = frame.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def sleep(ticks: Union[float, int] = 0):
    """
    Sleep a task.
    :param ticks: if it sleep randomly between 1 and 10 ticks.
    :return:
    """

    if not ticks:
        await asyncio.sleep(0)
    else:
        for _ in range(0, round(ticks)):
            await asyncio.sleep(0)

import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Dict, NoReturn, Optional, Tuple, Union

from space_game.settings import ContolSettings


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

    def __and__(self, other: 'MapObject') -> bool:
        return self.intersect(other) or other.intersect(self)


async def sleep(ticks: Union[float, int] = 0) -> NoReturn:
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
               negative: Optional[bool] = False) -> NoReturn:
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


def get_garbage_delay_tics(year: int) -> Union[None, int]:
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2

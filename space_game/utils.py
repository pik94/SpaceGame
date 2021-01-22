import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Dict, NoReturn, Optional, Tuple, Union

from space_game.settings import ContolSettings
from space_game.space_game import Frame


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

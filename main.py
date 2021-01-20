import asyncio
import curses
import itertools
from pathlib import Path
import random
import time
from typing import Dict, Optional, Tuple, Union


TIC_TIMEOUT = 0.1
STARS = ['+', '*', '.', ':']

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

# The higher the coefficient, the more stars on the sky.
# Should be more than 0
STAR_COEFF = 0.25


def read_frames() -> Dict[str, str]:
    """
    Read frames from the files and returns them in a string representation.
    :return: A dict where a key is a file name without suffix and a value is
        a string representing the frame.
    """

    frames = {}
    frame_paths = Path.cwd() / 'frames'
    for path in frame_paths.glob('*'):
        with open(path, 'r') as file:
            frames[path.stem] = ''.join(file)
    return frames


def read_controls(canvas) -> Tuple[int, int, bool]:
    """Read keys pressed and returns tuple with controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas,
               start_row: int,
               start_column: int,
               text: str,
               negative: Optional[bool] = False):
    """
    Draw multiline text fragment on canvas,
    erase text instead of drawing if negative=True is specified.
    """

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner
            # of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text: str) -> Tuple[int, int]:
    """
    Calculate size of multiline text fragment, return pair — number
    of rows and columns.
    :returns: a row and a column sizes
    """

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def fire(canvas,
               start_row: int,
               start_column: int,
               rows_speed: Optional[float] = -0.3,
               columns_speed: Optional[int] = 0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 1 < row < max_row and 1 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas,
                            frames: Dict[str, str],
                            start_row: int,
                            start_column: int,
                            row_speed: Optional[int] = 1,
                            column_speed: Optional[int] = 1):
    """
    A coroutine for drawing and moving the spaceship.
    :param canvas:
    :param frames: a dict with all frames for the game
    :param start_row: a start row point for the spaceship
    :param start_column: a start column point for the spaceship
    :param row_speed: row's speed
    :param column_speed: column's speed
    :return:
    """

    row, col = start_row, start_column
    frame_row_size, frame_col_size = get_frame_size(frames['rocket_frame_1'])
    window_height, window_width = canvas.getmaxyx()
    # Compute correct window sizes including borders
    window_height -= 1
    window_width -= 1
    spaceship_frames = [frames['rocket_frame_1'], frames['rocket_frame_2']]
    for frame in itertools.cycle(spaceship_frames):
        draw_frame(canvas, row, col, frame)
        await sleep(1)
        draw_frame(canvas, row, col, frame, negative=True)

        rows_direction, cols_direction, space_pressed = read_controls(canvas)
        rows_direction *= row_speed
        cols_direction *= column_speed

        if row + rows_direction <= 0:
            row = 1
        elif row + rows_direction + frame_row_size > window_height:
            row = window_height - frame_row_size
        else:
            row += rows_direction

        if col + cols_direction <= 0:
            col = 1
        elif col + cols_direction + frame_col_size >= window_width:
            col = window_width - frame_col_size
        else:
            col += cols_direction


async def sleep(ticks: Union[float, int] = 0):
    """
    Sleep a task.
    :param ticks: if it sleep randomly between 1 and 10 ticks.
    :return:
    """
    if not ticks:
        ticks = random.randint(1, 10)
    for _ in range(0, ticks):
        await asyncio.sleep(0)


async def blink(canvas,
                row: int,
                column: int,
                symbol: Optional[str] = '*'):
    """
    Draw a blinking symbol.
    """
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep()

        canvas.addstr(row, column, symbol)
        await sleep()

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep()

        canvas.addstr(row, column, symbol)
        await sleep()


def run_event_loop(canvas):
    curses.curs_set(False)

    canvas.border()
    canvas.nodelay(True)

    window_height, window_width = canvas.getmaxyx()

    # Compute correct window sizes without border lines
    window_height -= 2
    window_width -= 2

    frames = read_frames()

    if STAR_COEFF <= 0:
        raise ValueError('START_COEFF should be more than 0.')

    n_stars = int((window_height*window_width) * STAR_COEFF)
    coordinates = {
        (random.randint(1, window_width), random.randint(1, window_height))
        for _ in range(0, n_stars)
    }

    coroutines = [blink(canvas, row=y, column=x, symbol=random.choice(STARS))
                  for x, y in coordinates]
    coroutines.append(animate_spaceship(canvas,
                                        frames=frames,
                                        start_row=window_height // 2,
                                        start_column=window_width // 2,
                                        row_speed=2,
                                        column_speed=2))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        if not coroutines:
            break

        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(run_event_loop)

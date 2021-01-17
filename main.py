import curses
import random
import time
from typing import Optional, Union

import asyncio


TIC_TIMEOUT = 0.1
STARS = ['+', '*', '.', ':']
N_SAMPLES = 100
BLINK_TIMES = 100


async def sleep(seconds: Union[float, int] = 0):
    if not seconds:
        seconds = random.randint(1, 10)
    for _ in range(0, seconds):
        await asyncio.sleep(0)


async def blink(canvas,
                row: int,
                column: int,
                times: Optional[int] = BLINK_TIMES,
                symbol: Optional[str] = '*'):
    for _ in range(0, times):
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep()

        canvas.addstr(row, column, symbol)
        await sleep()

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep()

        canvas.addstr(row, column, symbol)
        await sleep()


def draw(canvas):
    curses.curs_set(False)
    canvas.border()

    y_max, x_max = canvas.getmaxyx()
    y_max -= 2
    x_max -= 2

    n_samples = N_SAMPLES
    while n_samples > y_max*x_max:
        n_samples = n_samples // 2

    coroutines = {}
    for _ in range(0, n_samples):
        x = random.randint(1, x_max)
        y = random.randint(1, y_max)
        if (x, y) in coroutines:
            continue

        coroutines[(x, y)] = blink(canvas, row=y, column=x, times=10,
                                   symbol=random.choice(STARS))

    coroutines = list(coroutines.values())
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
    curses.wrapper(draw)

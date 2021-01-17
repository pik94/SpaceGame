import curses
import time

import asyncio


TIC_TIMEOUT = 0.1


async def sleep(seconds):
    for _ in range(0, int(seconds * 10)):
        await asyncio.sleep(0)


async def blink(canvas, row=5, column=10, times=3, symbol='*'):
    for _ in range(0, times):
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(2)

        canvas.addstr(row, column, symbol)
        await sleep(0.3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(0.5)

        canvas.addstr(row, column, symbol)
        await sleep(0.3)


def draw(canvas):
    curses.curs_set(False)
    canvas.border()

    coroutines = [
        blink(canvas, 1, col, times=10)
        for col in range(1, 11, 2)
    ]
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

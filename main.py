import curses
import time

import asyncio


async def blink(canvas, row=5, column=10, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(False)
    row, column = (5, 20)
    canvas.border()
    coroutine = blink(canvas, row, column)

    for _ in range(0, 20):
        coroutine.send(None)
        canvas.refresh()
    time.sleep(5)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

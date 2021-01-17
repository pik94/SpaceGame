import curses

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
    canvas.border()

    coroutines = [
        blink(canvas, 1, col)
        for col in range(1, 11, 2)
    ]

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

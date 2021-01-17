import curses
import time


def twinkle(canvas, row=5, column=20, pause=2, flag=None):
    if flag:
        canvas.addstr(row, column, '*', flag)
    else:
        canvas.addstr(row, column, '*')
    canvas.refresh()
    time.sleep(pause)


def draw(canvas):
    curses.curs_set(False)
    row, column = (5, 20)
    canvas.border()
    while True:
        twinkle(canvas, row, column, pause=2, flag=curses.A_DIM)
        twinkle(canvas, row, column, pause=0.3)
        twinkle(canvas, row, column, pause=0.5, flag=curses.A_BOLD)
        twinkle(canvas, row, columnpause=0.3)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

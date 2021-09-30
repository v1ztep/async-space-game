import asyncio
import curses
import time


def draw(canvas):
    row, column = (5, 20)
    curses.curs_set(False)
    canvas.border()

    coroutines_blink = [
        blink(canvas, row, column, symbol='*') for column in range(10, 20, 2)
    ]
    while True:
        for coroutine in coroutines_blink.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines_blink.remove(coroutine)
        if len(coroutines_blink) == 0:
            break
        canvas.refresh()
        time.sleep(1)


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)


def show_symbol(canvas, row, column, symbol, sleep_time, mode=curses.A_NORMAL):
    canvas.addstr(row, column, symbol, mode)
    canvas.refresh()
    time.sleep(sleep_time)


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()

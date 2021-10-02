import asyncio
import curses
import time
import random


def draw(canvas):
    curses.curs_set(False)
    canvas.border()

    rows = canvas.getmaxyx()[0] - 2
    columns = canvas.getmaxyx()[1] - 2
    symbols = ('+', '*', '.', ':')

    coroutines_blink = [
        blink(
            canvas, random.randint(1, rows),
            random.randint(1, columns), random.choice(symbols)
        ) for _ in range(150)
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
        time.sleep(0.1)


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for star in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for star in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for star in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for star in range(3):
            await asyncio.sleep(0)


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()

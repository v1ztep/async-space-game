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
        ) for _ in range(200)
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
    min_time_delay = 0
    max_time_delay = 20
    while True:
        blink_delay = random.randint(min_time_delay, max_time_delay)
        for star in range(20+blink_delay):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        for star in range(3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)

        for star in range(5):
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await asyncio.sleep(0)

        for star in range(3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()

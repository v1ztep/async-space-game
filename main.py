import asyncio
import curses
import random
import time
from itertools import cycle
from pathlib import Path

from curses_tools import draw_frame
from curses_tools import get_frame_size
from curses_tools import read_controls
from obstacles import Obstacle
from obstacles import show_obstacles
from physics import update_speed

COROUTINES = []
OBSTACLES = []


def draw(canvas):
    garbage_delay = 7
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)

    rows = canvas.getmaxyx()[0] - 2
    columns = canvas.getmaxyx()[1] - 2
    symbols = ('+', '*', '.', ':')

    global COROUTINES
    COROUTINES.extend([
        blink(
            canvas, random.randint(1, rows),
            random.randint(1, columns), random.choice(symbols)
        ) for _ in range(200)
    ])
    COROUTINES.append(animate_spaceship(canvas, rows, columns))
    COROUTINES.append(
        fill_orbit_with_garbage(canvas, columns, garbage_delay)
    )

    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        if len(COROUTINES) == 0:
            break
        canvas.refresh()
        time.sleep(0.1)


async def blink(canvas, row, column, symbol='*'):
    min_time_delay = 5
    max_time_delay = 30
    while True:
        blink_delay = random.randint(min_time_delay, max_time_delay)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(tics=blink_delay)

        canvas.addstr(row, column, symbol)
        await sleep(tics=3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(tics=5)

        canvas.addstr(row, column, symbol)
        await sleep(tics=3)


async def fire(
        canvas, start_row, start_column,
        rows_speed=-0.5, columns_speed=0
):
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


async def animate_spaceship(canvas, rows, columns):
    rocket_frames = (rocket_frame_1, rocket_frame_2)
    start_row, start_column = rows / 2, (columns / 2) - 2
    row_speed = column_speed = 0
    for frame in cycle(rocket_frames):
        draw_frame(canvas, start_row, start_column, frame)
        await asyncio.sleep(0)
        draw_frame(
            canvas, start_row, start_column, frame, negative=True
        )

        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(
            row_speed, column_speed, rows_direction, columns_direction
        )
        start_row, start_column = start_row + row_speed, \
                                  start_column + column_speed

        frame_size_row, frame_size_column = get_frame_size(frame)
        if start_row < 1:
            start_row = 1
        elif start_row > rows - frame_size_row:
            start_row = rows - frame_size_row + 1

        if start_column < 1:
            start_column = 1
        elif start_column > columns - frame_size_column:
            start_column = columns - frame_size_column + 1

        if space_pressed:
            global COROUTINES
            COROUTINES.append(fire(
                canvas, start_row, start_column + 2, rows_speed=-1
            ))


async def fill_orbit_with_garbage(canvas, column, delay):
    while True:
        global COROUTINES
        COROUTINES.append(fly_garbage(
            canvas, column=random.randint(0, column),
            garbage_frame=random.choice(garbage_frames)
        ))
        await sleep(tics=delay)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    rows_number, columns_number = canvas.getmaxyx()
    column = max(column, 0)
    column = min(column, columns_number - 1)
    row = 0

    global OBSTACLES, COROUTINES
    frame_size_row, frame_size_column = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, frame_size_row, frame_size_column)
    OBSTACLES.append(obstacle)
    COROUTINES.append(show_obstacles(canvas, OBSTACLES))

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        obstacle.row = row
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        canvas.border()
    OBSTACLES.remove(obstacle)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


if __name__ == '__main__':
    with open('frames/rocket_frame_1.txt', encoding='utf-8') as frame_1:
        rocket_frame_1 = frame_1.read()
    with open('frames/rocket_frame_2.txt', encoding='utf-8') as frame_2:
        rocket_frame_2 = frame_2.read()

    garbage_frames = []
    frames_garbage_paths = Path('frames/trash').glob('*.txt')
    for path in frames_garbage_paths:
        with open(path, encoding='utf-8') as trash_frame:
            garbage_frames.append(trash_frame.read())

    curses.update_lines_cols()
    curses.wrapper(draw)

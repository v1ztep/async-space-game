import asyncio
import curses
import random
import time
from itertools import cycle
from pathlib import Path

from curses_tools import draw_frame
from curses_tools import get_frame_size
from curses_tools import read_controls
from explosion import explode
from game_scenario import get_garbage_delay_tics
from obstacles import Obstacle
from physics import update_speed
from game_scenario import PHRASES

COROUTINES = []
OBSTACLES = []
OBSTACLES_IN_LAST_COLLISIONS = []
YEAR = 1957
PHRASES = PHRASES


def draw(canvas):
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
    COROUTINES.append(fill_orbit_with_garbage(canvas, columns))
    COROUTINES.append(game_pace(canvas))

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


async def game_pace(canvas):
    global YEAR, PHRASES
    year_window = canvas.derwin(3, 6, 0, 0)
    while True:
        year_window.border()
        year_window.addstr(1, 1, str(YEAR), curses.A_DIM)
        if YEAR in PHRASES:
            canvas.addstr(1, 7, PHRASES[YEAR], curses.A_DIM)
        year_window.refresh()
        await sleep(tics=15)
        YEAR += 1


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

    # curses.beep() #####################################################################

    while 1 < row < max_row and 1 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        global OBSTACLES, OBSTACLES_IN_LAST_COLLISIONS
        for obstacle in OBSTACLES:
            if obstacle.has_collision(row, column):
                OBSTACLES_IN_LAST_COLLISIONS.append(obstacle)
                return
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

        global YEAR, COROUTINES
        if space_pressed and YEAR >= 2020:
            COROUTINES.append(fire(
                canvas, start_row, start_column + 2, rows_speed=-1
            ))

        global OBSTACLES
        for obstacle in OBSTACLES:
            if obstacle.has_collision(
                    start_row, start_column,
                    frame_size_row, frame_size_column
            ):
                await show_gameover(canvas, rows, columns)


async def show_gameover(canvas, rows, columns):
    frame_size_row, frame_size_column = get_frame_size(end_game_frame)
    row, column = (rows / 2) - (frame_size_row / 2), \
                  (columns / 2) - (frame_size_column / 2)
    while True:
        draw_frame(canvas, row, column, end_game_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, end_game_frame)


async def fill_orbit_with_garbage(canvas, column):
    while True:
        global COROUTINES, YEAR
        delay = get_garbage_delay_tics(YEAR)
        if delay:
            COROUTINES.append(fly_garbage(
                canvas, column=random.randint(0, column),
                garbage_frame=random.choice(garbage_frames)
            ))
            await sleep(tics=delay)
        else:
            await asyncio.sleep(0)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    rows_number, columns_number = canvas.getmaxyx()
    column = max(column, 0)
    column = min(column, columns_number - 1)
    row = 2

    global OBSTACLES, OBSTACLES_IN_LAST_COLLISIONS
    frame_size_row, frame_size_column = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, frame_size_row, frame_size_column)
    OBSTACLES.append(obstacle)

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        obstacle.row = row
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        if obstacle in OBSTACLES_IN_LAST_COLLISIONS:
            OBSTACLES_IN_LAST_COLLISIONS.remove(obstacle)
            OBSTACLES.remove(obstacle)
            await explode(
                canvas, row + (frame_size_row/2), column + (frame_size_column/2)
            )
            return
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

    with open('frames/game_over.txt', encoding='utf-8') as file:
        end_game_frame = file.read()

    curses.update_lines_cols()
    curses.wrapper(draw)

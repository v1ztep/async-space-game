import asyncio
import curses
import random
import time
from itertools import cycle
from pathlib import Path

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

COROUTINES = []


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
    COROUTINES.append(fire(
        canvas, rows/2, columns/2,
        rows_speed=-0.5, columns_speed=0
    ))
    COROUTINES.append(
        fly_garbage(canvas, column=10, garbage_frame=garbage_frames[0])
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
        for star in range(blink_delay):
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
    rocket_speed = 5
    rocket_frames = (rocket_frame_1, rocket_frame_2)
    start_row, start_column = rows / 2, (columns / 2) - 2
    for frame in cycle(rocket_frames):
        draw_frame(canvas, start_row, start_column, frame)
        await asyncio.sleep(0)
        draw_frame(
            canvas, start_row, start_column, frame, negative=True
        )

        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        start_row += (rows_direction * rocket_speed)
        start_column += (columns_direction * rocket_speed)

        frame_size_rows, frame_size_columns = get_frame_size(frame)
        if start_row < 1:
            start_row = 1
        elif start_row > rows - frame_size_rows:
            start_row = rows - frame_size_rows + 1

        if start_column < 1:
            start_column = 1
        elif start_column > columns - frame_size_columns:
            start_column = columns - frame_size_columns + 1


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        canvas.border()


async def fill_orbit_with_garbage():
    pass


def get_frame_size(text):
    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


def read_controls(canvas):
    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1
        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1
        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1
        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1
        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue
        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue
            if column >= columns_number:
                break
            if symbol == ' ':
                continue
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


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

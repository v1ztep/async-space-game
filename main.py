import time
import curses


def draw(canvas):
    symbol = '*'
    row, column = (5, 20)
    curses.curs_set(False)
    canvas.border()

    while True:
        show_symbol(canvas, row, column, symbol, sleep_time=2,
                    mode=curses.A_DIM)
        show_symbol(canvas, row, column, symbol, sleep_time=0.3)
        show_symbol(canvas, row, column, symbol, sleep_time=0.5,
                    mode=curses.A_BOLD)
        show_symbol(canvas, row, column, symbol, sleep_time=0.3)


def show_symbol(canvas, row, column, symbol, sleep_time, mode=curses.A_NORMAL):
    canvas.addstr(row, column, symbol, mode)
    canvas.refresh()
    time.sleep(sleep_time)


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)


if __name__ == '__main__':
    main()

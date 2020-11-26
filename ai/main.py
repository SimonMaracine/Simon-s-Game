import time
import datetime
from typing import Optional, List
from enum import Enum, auto

import mss
import pynput
import numpy as np
from PIL import Image

BACKGROUND_COLOR_OF_GAME = (20, 20, 60)


class Tile(Enum):
    GREEN = (392, 264)  # These are tile positions
    RED = (632, 264)
    YELLOW = (392, 504)
    PURPLE = (632, 504)


class State(Enum):
    WAITING_TO_START = auto()
    LOOKING_FOR_HIGHLIGHT = auto()
    DOING_PATTERN = auto()


running = True
state = State.WAITING_TO_START
level_reached = 0
start_time: Optional[datetime.datetime] = None
mouse: Optional[pynput.mouse.Controller] = None


def keyboard_on_release(key):
    global state, running, start_time

    if key == pynput.keyboard.Key.esc:
        print("Printing info and closing the program...")
        running = False
    elif key == pynput.keyboard.Key.space:
        print("Starting...")
        start_time = datetime.datetime.now()
        print(start_time)
        state = State.LOOKING_FOR_HIGHLIGHT


def get_window_position(pixels: np.array, window_width: int, window_height: int) -> tuple:
    for j in range(0, window_height):
        for i in range(0, window_width):
            if tuple(pixels[j][i]) == BACKGROUND_COLOR_OF_GAME:
                for k in range(0, 1023):
                    if not tuple(pixels[j][i + k]) == BACKGROUND_COLOR_OF_GAME:
                        break
                return i, j

    raise RuntimeError("Couldn't find the program window")


def get_screen_pixels(sct: mss.mss, monitor: dict) -> np.array:
    data = sct.grab(monitor)
    image = Image.frombytes("RGB", (data.width, data.height), data.rgb)
    pixels = np.array(image)
    return pixels


def check_for_white(color: tuple) -> bool:
    if color[0] > 210 and color[1] > 210 and color[2] > 210:
        return True
    else:
        return False


def exit_program():
    print("Started on " + str(start_time))
    now = datetime.datetime.now()
    print("Now is " + str(now))
    print("Elapsed time is " + str(now - start_time))

    print(f"Reached level {level_reached} (If got it wrong, then {level_reached - 1})")


def main():
    global mouse, state, level_reached

    sct = mss.mss()
    monitor = {"top": 0, "left": 0, "width": 1600, "height": 900}
    print(f"Screen coordinates checked: {monitor}")

    window_pos = get_window_position(get_screen_pixels(sct, monitor), 1600, 900)
    print("Found program window")
    print(f"Game window position: {window_pos}")

    keyboard_listener = pynput.keyboard.Listener(on_release=keyboard_on_release)
    keyboard_listener.start()
    mouse = pynput.mouse.Controller()

    pattern: List[Tile] = []
    print("Starting main loop...")
    print("Press SPACE to start")

    while running:
        if state == State.WAITING_TO_START:
            pass  # There is nothing to do for now
        elif state == State.LOOKING_FOR_HIGHLIGHT:
            pixels = get_screen_pixels(sct, monitor)

            green = pixels[window_pos[1] + Tile.GREEN.value[1], window_pos[0] + Tile.GREEN.value[0]]
            red = pixels[window_pos[1] + Tile.RED.value[1], window_pos[0] + Tile.RED.value[0]]
            yellow = pixels[window_pos[1] + Tile.YELLOW.value[1], window_pos[0] + Tile.YELLOW.value[0]]
            purple = pixels[window_pos[1] + Tile.PURPLE.value[1], window_pos[0] + Tile.PURPLE.value[0]]

            for color, tile in zip((green, red, yellow, purple), Tile):
                if check_for_white(color):
                    pattern.append(tile)
                    print(f"Detected {tile}")
                    state = State.DOING_PATTERN
                    time.sleep(0.3)
        elif state == State.DOING_PATTERN:
            pattern_length = len(pattern)

            for i, tile in enumerate(pattern):
                mouse.position = (window_pos[0] + tile.value[0], window_pos[1] + tile.value[1])
                mouse.press(pynput.mouse.Button.left)
                mouse.release(pynput.mouse.Button.left)
                print(f"Pressed {tile}")
                if i != pattern_length - 1:
                    time.sleep(0.18)
                else:
                    print("----- Done pattern -----")
                    level_reached += 1
                    time.sleep(0.2)

            state = State.LOOKING_FOR_HIGHLIGHT

    sct.close()
    exit_program()


if __name__ == "__main__":
    main()

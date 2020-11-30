import time
import datetime
import os
import json
import threading
import sys
from typing import Optional, List
from enum import Enum, auto

import mss
import pynput
import screeninfo
import numpy as np
from PIL import Image

BACKGROUND_COLOR_OF_GAME = (20, 20, 60)
LOG_FILE_NAME = "AI_LOG"


class Tile(Enum):
    # These are the tiles' middle positions relative to the origin of the window
    GREEN = (392, 264)
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
end_time: Optional[datetime.datetime] = None
mouse = pynput.mouse.Controller()
wait = threading.Event()


def keyboard_on_release(key):
    global state, running, start_time

    if key == pynput.keyboard.Key.esc:
        print("Printing and dumping information and closing the program...")
        wait.set()
        running = False
    elif key == pynput.keyboard.Key.space:
        if state == State.WAITING_TO_START:
            print("Starting AI...")
            wait.set()
            start_time = datetime.datetime.now()
            state = State.LOOKING_FOR_HIGHLIGHT


def get_window_position(pixels: np.ndarray, monitor_width: int, monitor_height: int) -> tuple:
    for j in range(0, monitor_height):
        for i in range(0, monitor_width):
            if tuple(pixels[j][i]) == BACKGROUND_COLOR_OF_GAME:
                try:
                    for k in range(0, 1023):
                        if not tuple(pixels[j][i + k]) == BACKGROUND_COLOR_OF_GAME:
                            break
                except IndexError:
                    raise RuntimeError("Bad window position; please place the game's window completely on "
                                       "your leftmost monitor (which has the origin)")

                return i, j

    raise RuntimeError("Couldn't find the program window")


def get_monitor_size() -> tuple:
    for monitor in screeninfo.get_monitors():
        if monitor.x == 0 and monitor.y == 0:  # This is how I know that it's the leftmost monitor
            return monitor.width, monitor.height

    raise RuntimeError("Couldn't detect monitor size")


def get_screen_pixels(sct: mss.mss, portion: dict) -> np.ndarray:
    data = sct.grab(portion)
    image = Image.frombytes("RGB", (data.width, data.height), data.rgb)
    pixels = np.array(image)
    return pixels


def check_for_white(color: np.ndarray) -> bool:
    if color[0] > 180 and color[1] > 180 and color[2] > 180:
        return True
    else:
        return False


def on_exit():
    global end_time

    if state != State.WAITING_TO_START:
        print("Started on " + str(start_time))
        end_time = datetime.datetime.now()
        print("Now is " + str(end_time))
        print("Elapsed time is " + str(end_time - start_time))

        print(f"Reached level {level_reached} (If got it wrong, then {level_reached - 1})")
    else:
        print("No information printed")


def dump_info_to_file(start_time_: datetime.datetime, end_time_: datetime.datetime, level_reached_: int,
                      pattern: List[Tile]):
    if state == State.WAITING_TO_START:
        print("No information dumped")
        return

    log_number = 0

    # Find out how to name the log file
    items = os.listdir(".")
    for item in items:
        if LOG_FILE_NAME in item and ".json" in item and os.path.isfile(item):
            item = item.rstrip(".json")
            try:
                number_string = item[6:]
                if not number_string:
                    number = 0
                else:
                    number = int(number_string)
            except ValueError:
                continue
            log_number = max(log_number, number + 1)

    if log_number == 0:
        file_name = LOG_FILE_NAME + ".json"
    else:
        file_name = LOG_FILE_NAME + str(log_number) + ".json"

    with open(file_name, "w") as file:
        data = {
            "start_time": str(start_time_),
            "end_time": str(end_time_),
            "delta_time": str(end_time_ - start_time_),
            "level_reached": level_reached_,
            "pattern": [str(tile) for tile in pattern]
        }

        json.dump(data, file, indent=4)

    print(f"Information dumped in {file_name}")


def main(args: list):
    global mouse, state, level_reached

    if len(args) < 2:
        print("Getting screen coordinates...")
        try:
            width, height = get_monitor_size()
        except screeninfo.screeninfo.ScreenInfoError:
            print("Error getting the monitor's size; pass the resolution yourself as the program's arguments",
                  file=sys.stderr)
            return
    else:
        try:
            width, height = int(args[1]), int(args[2])
        except (ValueError, IndexError):
            print("Pass two whole numbers as arguments (eg. python AI.py 1600 900)", file=sys.stderr)
            return

        if width <= 0 or height <= 0:
            print("Width or height <= 0 is invalid", file=sys.stderr)
            return

    monitor = {"top": 0, "left": 0, "width": width, "height": height}
    print(f"Screen coordinates: {monitor}")

    sct = mss.mss()

    print("Getting window position...")
    window_pos = get_window_position(get_screen_pixels(sct, monitor), width, height)
    print(f"Found window position: {window_pos}")
    print("DON'T move the window now")

    window_portion = {"top": window_pos[1] + 164 + 200 - 20,
                      "left": window_pos[0] + 292 + 200 - 20,
                      "width": 40 + 20 * 2,
                      "height": 40 + 20 * 2}  # These are the coordinates for the bounding box of the screen portion
    print(f"Capture portion of the screen: {window_portion}")

    pynput.keyboard.Listener(on_release=keyboard_on_release).start()

    pattern: List[Tile] = []
    print("Starting main loop...")
    print("Press SPACE to start")
    print("Press ESCAPE to exit")

    while running:
        if state == State.WAITING_TO_START:
            wait.wait(10.0)  # There is nothing to do
        elif state == State.LOOKING_FOR_HIGHLIGHT:
            pixels = get_screen_pixels(sct, window_portion)

            green = pixels[0][0]
            red = pixels[0][79]
            yellow = pixels[79][0]
            purple = pixels[79][79]

            for color, tile in zip((green, red, yellow, purple), Tile):
                if check_for_white(color):
                    pattern.append(tile)
                    print(f"Detected {tile}")
                    state = State.DOING_PATTERN
                    time.sleep(0.3)
        elif state == State.DOING_PATTERN:
            pattern_length = len(pattern)

            for i, tile in enumerate(pattern):
                if not running:  # If ESCAPE was pressed, exit immediately without doing the rest of the pattern
                    break
                mouse.position = (window_pos[0] + tile.value[0], window_pos[1] + tile.value[1])
                mouse.press(pynput.mouse.Button.left)
                mouse.release(pynput.mouse.Button.left)
                print(f"Pressed {tile}")
                if i != pattern_length - 1:
                    time.sleep(0.18)
                else:
                    print("----- Done pattern -----")
                    level_reached += 1
                    time.sleep(0.24)

            state = State.LOOKING_FOR_HIGHLIGHT

    sct.close()
    on_exit()
    dump_info_to_file(start_time, end_time, level_reached, pattern)


if __name__ == "__main__":
    main(sys.argv)

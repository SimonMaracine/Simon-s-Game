from random import choice
from typing import Optional, List
from enum import Enum, auto
from os.path import join
from threading import Timer

import pygame

WIDTH = 1024
HEIGHT = 768
TILE_WIDTH = 200
running = True
window: Optional[pygame.Surface] = None
clock: Optional[pygame.time.Clock] = None


class Color(Enum):
    GREEN = (0, 200, 0)
    RED = (200, 0, 0)
    YELLOW = (190, 190, 0)
    PURPLE = (128, 0, 128)


class GameState(Enum):
    BEGINNING = auto()
    IN_GAME = auto()
    GAME_OVER = auto()


error_background = 0  # The amount of red

level = 0
state = GameState.BEGINNING  # This is true only at the start of the program
tiles = []

pattern_to_check_index = 0
moves_so_far: List[Color] = []


class Tile:

    def __init__(self, x: int, y: int, color: Color, sound_path: str):
        self.x = x
        self.y = y
        self.color = color.value
        self.width = TILE_WIDTH

        self.sound = pygame.mixer.Sound(sound_path)
        self.white_color = 0

    def update(self):
        if self.white_color > 0:
            self.white_color -= 10
            self.white_color = max(self.white_color, 0)  # Clamp to 0

    def draw(self, surface: pygame.Surface):
        color = (min(self.color[0] + self.white_color, 255),
                 min(self.color[1] + self.white_color, 255),
                 min(self.color[2] + self.white_color, 255))
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.width), 0, 40)
        pygame.draw.rect(surface, (0, 0, 0), (self.x, self.y, self.width, self.width), 6, 40)

    def press(self, pos: tuple):
        if self.x + self.width > pos[0] > self.x and \
                self.y + self.width > pos[1] > self.y:
            self.sound.play()
            self._blink()
            press(self.color)

    def play(self):
        self.sound.play()
        self._blink()

    def _blink(self):
        self.white_color = 255


def start():  # Or "restart"
    global pattern_to_check_index, state, level

    state = GameState.IN_GAME
    moves_so_far.clear()
    pattern_to_check_index = 0
    level = 0

    Timer(0.7, show_next_move).start()


def show_next_move():
    global pattern_to_check_index

    pattern_to_check_index = 0
    tile = choice(tiles)
    moves_so_far.append(tile.color)
    tile.play()


def press(color: Color):
    global pattern_to_check_index, state, level, error_background

    if state == GameState.IN_GAME:  # Ensure not playing when it's not started
        try:
            got_it_right = color == moves_so_far[pattern_to_check_index]
        except IndexError:  # This happens when trying to press when it's not ready yet
            return

        if got_it_right:
            pattern_to_check_index += 1

            if pattern_to_check_index == len(moves_so_far):
                Timer(0.7, show_next_move).start()
                level += 1
        else:
            state = GameState.GAME_OVER
            blink_red()


def blink_red():
    global error_background
    error_background = 255


def main():
    global running, window, clock, error_background

    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simon's Game")
    clock = pygame.time.Clock()

    green = Tile(WIDTH // 2 - TILE_WIDTH - 20, HEIGHT // 2 - TILE_WIDTH - 20, Color.GREEN, join("data", "green.wav"))
    red = Tile(WIDTH // 2 + 20, HEIGHT // 2 - TILE_WIDTH - 20, Color.RED, join("data", "red.wav"))
    yellow = Tile(WIDTH // 2 - TILE_WIDTH - 20, HEIGHT // 2 + 20, Color.YELLOW, join("data", "yellow.wav"))
    purple = Tile(WIDTH // 2 + 20, HEIGHT // 2 + 20, Color.PURPLE, join("data", "purple.wav"))
    tiles.append(green)
    tiles.append(red)
    tiles.append(yellow)
    tiles.append(purple)

    font = pygame.font.SysFont("", 60, True)
    begin_instructions = font.render("Press Any Key To Begin", True, (255, 255, 255))
    restart_instructions = font.render("Press Any Key To Restart", True, (255, 255, 255))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if state != GameState.IN_GAME and running is not False:
                    start()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT:
                    for tile in tiles:
                        tile.press(event.pos)

        background_color = (min(20 + error_background, 255), 20, 60)
        window.fill(background_color)

        for tile in tiles:
            tile.update()
            tile.draw(window)

        if state == GameState.BEGINNING:
            window.blit(begin_instructions, (WIDTH // 2 - begin_instructions.get_width() // 2, 65))
        elif state == GameState.IN_GAME:
            level_text = font.render(f"Level {level}", True, (255, 255, 255))
            window.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 65))
        elif state == GameState.GAME_OVER:
            game_over_text = font.render(f"Game Over, Level {level}", True, (255, 255, 255))
            window.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, 40))
            window.blit(restart_instructions, (WIDTH // 2 - restart_instructions.get_width() // 2, 90))

        if error_background > 0:
            error_background -= 10
            error_background = max(error_background, 0)  # Clamp to 0

        pygame.display.flip()
        clock.tick(60)

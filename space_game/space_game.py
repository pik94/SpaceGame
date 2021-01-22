import asyncio
import curses
import itertools
from pathlib import Path
import random
import time
from typing import NoReturn, Optional, Union

from space_game.physics import update_speed
from space_game.settings import MapSettings, TIC_TIMEOUT
from space_game.utils import (
    draw_frame, get_garbage_delay_tics, read_objects,
    read_controls, sleep, Frame, MapObject
)


class SpaceGame:
    def __init__(self):
        self._coroutines = []
        self._all_frames = read_objects(Path.cwd() / 'frames')
        self._dynamic_objects = {}

        self._canvas = None
        self._current_year = MapSettings.START_YEAR

    def run(self) -> NoReturn:
        assert MapSettings.STAR_COEFF > 0

        curses.update_lines_cols()
        curses.wrapper(self._run_event_loop)

    def _run_event_loop(self, canvas) -> NoReturn:
        curses.curs_set(False)

        self._canvas = canvas
        self._canvas.border()
        self._canvas.nodelay(True)

        max_y, max_x = self._canvas.getmaxyx()
        # Compute correct window sizes without border lines
        max_y -= 2
        max_x -= 2

        n_stars = int((max_y*max_x) * MapSettings.STAR_COEFF)
        coordinates = {(random.randint(1, max_x), random.randint(1, max_y))
                       for _ in range(0, n_stars)}
        self._coroutines = [
            self.blink(MapObject(
                frame=Frame(random.choice(MapSettings.STAR_SET)),
                start_x=x,
                start_y=y)
            )
            for x, y in coordinates
        ]
        self._coroutines.append(self.animate_spaceship(start_y=10, start_x=10))
        self._coroutines.append(self.fill_orbit_with_garbage())
        self._coroutines.append(self.draw_timer())
        self._coroutines.append(self.increase_year())

        while True:
            for coroutine in self._coroutines.copy():
                try:
                    coroutine.send(None)
                    self._canvas.refresh()
                except StopIteration:
                    self._coroutines.remove(coroutine)
            if not self._coroutines:
                break

            time.sleep(TIC_TIMEOUT)

    async def fire(self,
                   start_x: int,
                   start_y: int,
                   x_speed: Optional[Union[float, int]] = 0,
                   y_speed: Optional[Union[float, int]] = -0.3) -> NoReturn:
        """
        Display animation of gun shot, direction and speed
        can be specified.
        """

        x, y = start_x, start_y
        self._canvas.addstr(round(y), round(x), '*')
        await sleep(0)

        self._canvas.addstr(round(y), round(x), 'O')
        await sleep(0)
        self._canvas.addstr(round(y), round(x), ' ')

        x += x_speed
        y += y_speed

        symbol = '-' if x_speed else '|'

        max_y, max_x = self._canvas.getmaxyx()
        max_y, max_x = max_y - 1, max_x - 1

        curses.beep()
        fire_shot_object = MapObject(Frame(symbol), x, y)
        while 1 < y < max_y and 1 < x < max_x:
            self._canvas.addstr(round(y), round(x), symbol)
            await sleep(0)
            self._canvas.addstr(round(y), round(x), ' ')
            fire_shot_object.change_coordinates(x + x_speed, y + y_speed)
            for obj_id, obj in self._dynamic_objects.items():
                if obj_id.startswith('rubbish') and obj & fire_shot_object:
                    draw_frame(self._canvas, obj.x, obj.y, obj.frame,
                               negative=True)
                    self._dynamic_objects.pop(obj_id)
                    await self.explode(obj.x, obj.y)
                    return

            y += y_speed
            x += x_speed

    async def animate_spaceship(self,
                                start_x: int,
                                start_y: int) -> NoReturn:
        """
        A coroutine for drawing and moving the spaceship.
        :param start_x: a start x (column) point for the spaceship
        :param start_y: a start y (row) point for the spaceship
        :return:
        """

        x_speed, y_speed = 0, 0
        max_y, max_x = self._canvas.getmaxyx()
        # Compute correct window sizes including borders
        max_x -= 1
        max_y -= 1

        spaceship_frames = self._all_frames['spaceship']
        spaceship = MapObject(
            frame=spaceship_frames['rocket_frame_1'],
            start_x=start_x,
            start_y=start_y
        )
        self._dynamic_objects['spaceship'] = spaceship

        for i in itertools.cycle([1, 2]):
            x, y = spaceship.current_coordinates()
            frame = spaceship_frames[f'rocket_frame_{i}']

            draw_frame(self._canvas, x, y, frame)
            for _ in range(0, 2):
                x_direction, y_direction, space_pressed = \
                    read_controls(self._canvas)
                x_speed, y_speed = update_speed(x_speed, y_speed, x_direction,
                                                y_direction)
                await sleep(1)
            draw_frame(self._canvas, x, y, frame, negative=True)

            if y + y_speed <= 1:
                y = 1
            elif y + y_speed + frame.height > max_y:
                y = max_y - frame.height
            else:
                y += y_speed

            if x + x_speed <= 1:
                x = 1
            elif x + x_speed + frame.width >= max_x:
                x = max_x - frame.width
            else:
                x += x_speed

            if space_pressed and self._current_year >= 2020:
                x_fire = round(x + spaceship.frame.width // 2)
                self._coroutines.append(self.fire(x_fire, y))

            spaceship.change_frame(frame)
            spaceship.change_coordinates(x, y)

            await self.check_game_over(spaceship, max_x, max_y)

    async def check_game_over(self,
                              spaceship: MapObject,
                              max_x: int,
                              max_y: int) ->NoReturn:
        """
        Check if the spaceship is hit to a rubbish. If it's "Game Over"
        is printed.
        :param spaceship:
        :param max_x: max x coordinate
        :param max_y: max y coordinate
        :return:
        """

        for obj_id, obj in self._dynamic_objects.items():
            if not obj_id.startswith('rubbish'):
                continue
            if spaceship & obj:
                while True:
                    draw_frame(self._canvas, max_x // 4, max_y // 2,
                               self._all_frames['other']['game_over'])
                    await sleep(0)

    async def blink(self, star: MapObject) -> NoReturn:
        """
        Draw a blinking symbol.
        """
        x, y = star.current_coordinates()
        symbol = star.frame.content
        while True:
            self._canvas.addstr(y, x, symbol, curses.A_DIM)
            await sleep(random.randint(1, 10))

            self._canvas.addstr(y, x, symbol)
            await sleep(random.randint(1, 10))

            self._canvas.addstr(y, x, symbol, curses.A_BOLD)
            await sleep(random.randint(1, 10))

            self._canvas.addstr(y, x, symbol)
            await sleep(random.randint(1, 10))

    async def fly_garbage(self,
                          rubbish_object: MapObject,
                          rubbish_id: str,
                          speed: Optional[float] = 0.5) -> NoReturn:
        """
        Animate garbage, flying from top to bottom.
        A start_x position will stay same, as specified on start.
        """

        max_y, max_x = self._canvas.getmaxyx()

        x, y = rubbish_object.current_coordinates()
        while y < max_y:
            if rubbish_id not in self._dynamic_objects:
                return

            rubbish_object.change_coordinates(x, y)
            draw_frame(self._canvas, x, y, rubbish_object.frame)
            await sleep(0)
            draw_frame(self._canvas, x, y, rubbish_object.frame, negative=True)
            y += speed

        self._dynamic_objects.pop(rubbish_id)

    async def fill_orbit_with_garbage(self) -> NoReturn:
        """
        This method produces rubbish on the map
        """

        # Wait for a year when the first rubbish will appear on the map
        delay_tick = get_garbage_delay_tics(self._current_year)
        while delay_tick is None:
            await sleep(5)
            delay_tick = get_garbage_delay_tics(self._current_year)

        rubbish_frames = [
            frame
            for name, frame in self._all_frames['rubbish'].items()
            if not name.startswith('rocket')
        ]

        max_y, max_x = self._canvas.getmaxyx()
        rubbish_count = 0

        # This variable shows how much rubbish can be on the map simultaneously
        max_rubbish_count = max_x * max_y // min(frame.height * frame.width
                                                 for frame in rubbish_frames)
        while True:
            produce_next = False
            frame = rubbish_frames[
                random.randint(0, len(rubbish_frames) - 1)]
            start_x = random.randint(-frame.width + 2, max_x - 2)
            start_y = -frame.height
            rubbish_object = MapObject(frame, start_x, start_y)

            # Check that a new rubbish sample does not overlap existing
            # If it does, try to produce another sample.
            for existing_object in self._dynamic_objects.values():
                if rubbish_object & existing_object:
                    produce_next = True
                    break

            if produce_next:
                continue

            if rubbish_count > max_rubbish_count:
                # Reset count because objects with old IDs disappeared
                rubbish_count = 0
            else:
                rubbish_count += 1
            rubbish_id = f'rubbish_{rubbish_count}'

            self._dynamic_objects[rubbish_id] = rubbish_object
            self._coroutines.append(self.fly_garbage(rubbish_object,
                                                     rubbish_id))
            await sleep(get_garbage_delay_tics(self._current_year))

    async def explode(self, x, y) -> NoReturn:
        explosion_frames = self._all_frames['explosion']
        curses.beep()
        for frame in explosion_frames.values():
            draw_frame(self._canvas, x, y, frame)
            await asyncio.sleep(0)
            draw_frame(self._canvas, x, y, frame, negative=True)
            await asyncio.sleep(0)

    async def draw_timer(self) -> NoReturn:
        max_y, max_x = self._canvas.getmaxyx()
        max_y -= 2
        max_x -= 2
        canvas = self._canvas.derwin(3, max_x // 2, max_y - 1, max_x // 2)

        n_prev_phrase_symbols = 0
        while True:
            msg = f'Year: {self._current_year}'
            phrase = MapSettings.PHRASES.get(self._current_year, "")
            if phrase:
                msg = f'{msg} - {phrase}'
                n_prev_phrase_symbols = len(phrase) + 3
            else:
                msg = f'{msg}{" " * n_prev_phrase_symbols}'
                n_prev_phrase_symbols = 0

            canvas.addstr(1, 1, msg)
            canvas.border()
            canvas.refresh()
            await sleep(0)

    async def increase_year(self) -> NoReturn:
        self._current_year = MapSettings.START_YEAR
        while True:
            await sleep(10)
            self._current_year += 1

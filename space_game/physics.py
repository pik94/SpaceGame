import math
from typing import Optional, Tuple


def _limit(value, min_value, max_value):
    """Limit value by min_value and max_value."""

    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def _apply_acceleration(speed, speed_limit, forward=True):
    """Change speed — accelerate or brake — according to force direction."""

    speed_limit = abs(speed_limit)

    speed_fraction = speed / speed_limit

    # если корабль стоит на месте, дергаем резко
    # если корабль уже летит быстро, прибавляем медленно
    delta = math.cos(speed_fraction) * 0.75

    if forward:
        result_speed = speed + delta
    else:
        result_speed = speed - delta

    result_speed = _limit(result_speed, -speed_limit, speed_limit)

    # если скорость близка к нулю, то останавливаем корабль
    if abs(result_speed) < 0.1:
        result_speed = 0

    return result_speed


def update_speed(x_speed: float,
                 y_speed: float,
                 x_direction: int,
                 y_direction: int,
                 x_speed_limit: Optional[int] = 2,
                 y_speed_limit: Optional[int] = 2,
                 fading: Optional[float] = 0.8) -> Tuple[int, int]:
    """
    Update speed smoothly to make control handy for player. Return new speed
    value (row_speed, column_speed)

    rows_direction — is a force direction by row's axis. Possible values:
       -1 — if force pulls up
       0  — if force has no effect
       1  — if force pulls down
    columns_direction — is a force direction by column's axis. Possible values:
       -1 — if force pulls left
       0  — if force has no effect
       1  — if force pulls right
    """

    if y_direction not in (-1, 0, 1):
        raise ValueError(
            f'Wrong rows_direction value {y_direction}. Expects -1, 0 or 1.')

    if x_direction not in (-1, 0, 1):
        raise ValueError(
            f'Wrong columns_direction value {x_direction}. '
            f'Expects -1, 0 or 1.')

    if fading < 0 or fading > 1:
        raise ValueError(
            f'Wrong columns_direction value {fading}. '
            f'Expects float between 0 and 1.')

    # гасим скорость, чтобы корабль останавливался со временем
    y_speed *= fading
    x_speed *= fading

    y_speed_limit, x_speed_limit = abs(y_speed_limit), abs(
        x_speed_limit)

    if y_direction != 0:
        y_speed = _apply_acceleration(y_speed, y_speed_limit,
                                      y_direction > 0)

    if x_direction != 0:
        x_speed = _apply_acceleration(x_speed, x_speed_limit,
                                      x_direction > 0)

    return x_speed, y_speed

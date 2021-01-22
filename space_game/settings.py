TIC_TIMEOUT = 0.1


class MapSettings:
    STAR_SET = ['+', '*', '.', ':']

    # The higher the coefficient, the more stars on the sky.
    # Should be more than 0
    STAR_COEFF = 0.005

    # The higher the coefficient, the more stars on the sky.
    # Should be more or equal to 0
    RUBBISH_COEFF = 0
    START_YEAR = 1950

    PHRASES = {
        1957: "First Sputnik",
        1961: "Gagarin flew!",
        1969: "Armstrong got on the moon!",
        1971: "First orbital space station Salute-1",
        1981: "Flight of the Shuttle Columbia",
        1998: 'ISS start building',
        2011: 'Messenger launch to Mercury',
        2020: "Take the plasma gun! Shoot the garbage!",
    }


class ContolSettings:
    SPACE_KEY_CODE = 32
    LEFT_KEY_CODE = 260
    RIGHT_KEY_CODE = 261
    UP_KEY_CODE = 259
    DOWN_KEY_CODE = 258

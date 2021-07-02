import os, sys
import unittest

sys.path.append(os.getcwd())

from bunker.main import *

class HealthError(Exception):
    pass

def change_health(health: list=[], swap=False):
    """Если передано здоровье и параметр обменяться, то возващает текущее здоровье
    """
    if not isinstance(health, list):
        raise HealthError
    if health:
        if health[0] not in DATA['Состояние здоровья']:
            raise HealthError
        if health[1] < 1 or health[1] > 100:
            raise HealthError

    if health and swap:
        health, health = health, health
        return health
    elif health and not swap:
        health = health
    else:
        health = [random.choice(DATA['Состояние здоровья']), random.randint(1, 100)]
    return health


class TestChangeHealth(unittest.TestCase):
    def test_change_health_return_health(self, *args, **kwargs):
        self.assertIsInstance(change_health(*args, **kwargs), list)
        self.assertIsInstance(change_health(*args, **kwargs)[0], str)
        self.assertIn(change_health(*args, **kwargs)[0], DATA['Состояние здоровья'])
        self.assertIsInstance(change_health(*args, **kwargs)[1], int)
        self.assertGreaterEqual(change_health(*args, **kwargs)[1], 1)
        self.assertLessEqual(change_health(*args, **kwargs)[1], 100)
        

    def test_change_health_assept_health(self):
        health = [DATA['Состояние здоровья'][0], 1]
        change_health(health)
        self.test_change_health_return_health(change_health(health=health))
        health = [DATA['Состояние здоровья'][0], 100]
        change_health(health)
        self.test_change_health_return_health(change_health(health=health))


        health = [DATA['Состояние здоровья'][0], 0]
        with self.assertRaises(HealthError):
            change_health(health)

        health = [DATA['Состояние здоровья'][0], -1]
        with self.assertRaises(HealthError):
            change_health(health)

        health = [DATA['Состояние здоровья'][0], 101]
        with self.assertRaises(HealthError):
            change_health(health)

    def test_change_health_(self):
        pass
    def test_change_health_(self):
        pass


if __name__ == "__main__":
    unittest.main()
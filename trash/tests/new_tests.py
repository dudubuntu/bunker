import os, sys, pathlib
import unittest
import pytest

# sys.path.append(pathlib.Path(__file__).parent.parent)
print(str(pathlib.Path(__file__).parent.parent))
print(os.getcwd())
sys.path.append(pathlib.Path(__file__).parent.parent)
from main import *



class TestPlayer(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.player = Player()

    def test_init(self):
        self.assertIsInstance(self.player, Player)
        for attr_name in ['profession', 'health', 'bio', 'parameters', 'quality', 'phobia', 'bagage', 'hobby', 'skill', 'cards']:
            self.assertTrue(hasattr(self.player, attr_name))

    def test_change_bio(self):
        bio = self.player.change_bio()
        self.assertIsInstance(bio, list)

        self.assertIn(bio[0], DATA['Биологическая характеристика'])
        self.assertGreaterEqual(bio[1], 18)
        self.assertLessEqual(bio[1], 90)
        self.assertIsInstance(bio[2], bool)
        
        self.assertIs(bio, self.player.bio)
    
    def test_change_parameters(self):
        parameters = self.player.change_parameters()
        self.assertIsInstance(parameters, list)

        self.assertGreaterEqual(parameters[0], 140)
        self.assertLessEqual(parameters[0], 230)
        self.assertGreaterEqual(parameters[1], 40)
        self.assertLessEqual(parameters[1], 150)
        
        self.assertIs(parameters, self.player.parameters)

    def test_change_quality(self):
        quality = self.player.change_quality()
        self.assertIsInstance(quality, list)
        self.assertEqual(len(quality), 2)

        for q in quality:
            self.assertIn(q[0], DATA['Человеческое качество'])
            self.assertGreaterEqual(q[1], 1)
            self.assertLessEqual(q[1], 100)
        
        self.assertIs(quality, self.player.quality)
    

@pytest.mark.parametrize("args, expected_result", [
    # pytest.param((None, False), lambda health: isinstance(health, list), id='generate'),
    pytest.param(
        (['health', 'health'], False), ['health', 'health'], id='basic'
    ),
    pytest.param(
        (['swap', 'swap'], True), ['swap', 'swap'], id='swap'
    ),
])
def test_change_health(args, expected_result):
    player = Player()
    health = player.change_health(*args)
    assert player.health == expected_result





# if __name__ == '__main__':
    # pytest.main()
    # unittest.main()


# для некоторых тестов нужны циклы с раными параметрами
# если делать эти с помощью простых циклов, если упадет один тест из цикла
# упадет весь тест
# это решается с помощью параметризирования с pytest
# pytest умеет запускать тесты, написанные на unittest
# pytest умеет работать с обычными assert
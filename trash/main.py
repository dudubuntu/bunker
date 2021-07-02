import random
import os, sys

sys.path.append(os.getcwd())

from bunker.help import DATA


class Player:
    """
    profession: list -->    ['название', 'стаж']                    [str, int]
    health: list -->        ['название болезни', 'степень']         [str, str]
    bio: list -->           ['муж', 'возраст', 'бесплоден ли']      ['Мужчина'/'Женщина', int, bool]
    hobby: list -->         ['название', 'стаж']                    [str, int]
    quality: list -->       ['название', 'степень выраженности']    [str, int]
    cards: list -->         ['Первая карта', 'Вторая карта']        [str, str]
    """

    def __init__(self):
        self.change_bio()
        self.change_parameters()
        self.change_profession()
        self.change_health()
        self.change_quality()
        self.change_phobia()
        self.change_bagage()
        self.change_hobby()
        self.change_skill()
        
        first_card = random.choice(DATA['Карточки'])
        loc_data = []
        loc_data.extend(DATA['Карточки'])
        loc_data.remove(first_card)
        second_card = random.choice(loc_data)
        self.cards = [first_card, second_card]

    def __str__(self):
        str_card = f"{self.bio[0]} - {self.bio[1]} лет - {'Бесплоден' if self.bio[2] else 'Может иметь потомство'}\nРост - {self.parameters[0]}   Вес - {self.parameters[1]}\n{self.profession[0]}\n\tСтаж {self.profession[1]} лет\n"
        str_card += f"{self.health[0]} - степень {self.health[1]} %\nЧеловеческие качества:\n\t{self.quality[0][0]} - выражено на {self.quality[0][1]} %\n\t{self.quality[1][0]} - выражено на {self.quality[1][1]} %\n"
        str_card += f"Фобия: {self.phobia}\nДополнительный навык: {self.skill}\nХобби: {self.hobby[0]} - {self.hobby[1]} лет\n"
        str_card += f"Багаж: {self.bagage}\n\nПервая карточка: {self.cards[0]}\n\nВторая карточка: {self.cards[1]}"

        return str_card

    def change_profession(self, profession: list = None, swap=False):
        """Если передана профессия и параметр обменяться, то возващает текущую профессию
        """
        if profession is not None and swap:
            self.profession, profession = profession, self.profession
            return profession
        elif profession is not None and not swap:
            self.profession = profession
        else:
            self.profession = [random.choice(DATA['Профессия']), random.randint(0, self.bio[1] - 18)]
        return self.profession

    def change_health(self, health: list=None, swap=False):
        """Если передано здоровье и параметр обменяться, то возващает текущее здоровье
        """
        if health is not None and swap:
            self.health, health = health, self.health
            return health
        elif health and not swap:
            self.health = health
        else:
            self.health = [random.choice(DATA['Состояние здоровья']), random.randint(1, 100)]
        return self.health

    def make_full_health(self):
        self.health = ['Идеально здоров', 100]
        return self.health

    def change_bio(self):
        self.bio = [random.choice(DATA['Биологическая характеристика']), random.randint(18, 90), random.choice([True, True, True, False])]
        return self.bio

    def change_parameters(self):
        self.parameters = [random.randint(140, 230), random.randint(40, 150)]
        return self.parameters

    def change_quality(self):
        self.quality = [[random.choice(DATA['Человеческое качество']), random.randint(1, 100)],
                        [random.choice(DATA['Человеческое качество']), random.randint(1, 100)]]
        return self.quality

    def change_phobia(self):
        self.phobia = random.choice(DATA['Фобия'])
        return self.phobia

    def change_bagage(self):
        self.bagage = random.choice(DATA['Багаж'])
        return self.bagage

    def change_hobby(self):
        self.hobby = [random.choice(DATA['Хобби']), random.randint(0, self.bio[1] - 18)]
        return self.hobby

    def change_skill(self):
        self.skill = random.choice(DATA['Дополнительный навык'])
        return self.skill

class Game:
    def start_game(self):
        self.players_amount = int(input('Сколько игроков будет в игре? '))
        print('\n\n\n\n\n\n\n')

        self.players = []
        for i in range(self.players_amount):
            self.players.append(Player())
        self.show_players()

        print('Начало игры:\n\n\n')
        # print(random.choice(DATA['Локация']))
        print(random.choice(DATA['Бункер']))
        print(random.choice(DATA['Бункер']))
        print('\n\n\n')
        while True:
            print(f'[1 - {self.players_amount}] - показать игрока\ns - показать всех игроков\n\nУ всех:\n\tp - изменить профессии\n\th - изменить здоровье\n\tb - изменить биологические характеристики\n\tpar - изменить параметры\n\n')
            while True:
                command = input('Введите команду: ')
                if len(command) == 3:
                    self.change_all_parameters()
                else:
                    try:
                        command = int(command)
                    except BaseException:
                        if command == 's':
                            self.show_players()
                        elif command == 'p':
                            self.change_all_professions()
                        elif command == 'h':
                            self.change_all_health()
                        elif command == 'b':
                            self.change_all_bio()
                    else:
                        self.show_player(command)

                input('\n\nНажмите Enter, чтобы продолжить: ')
                break

    def show_player(self, i):
            print(self.players[i - 1])
            for j in range(10):
                print('\n')

    def show_players(self):
        for i in range(1, self.players_amount + 1):
            self.show_player(i)

    def change_all_professions(self):
        for i in range(self.players_amount):
            self.players[i].change_profession()

    def change_all_health(self):
        for i in range(self.players_amount):
            self.players[i].change_health()

    def change_all_bio(self):
        for i in range(self.players_amount):
            self.players[i].change_bio()

    def change_all_parameters(self):
        for i in range(self.players_amount):
            self.players[i].change_parameters()


# когда меняются профессиями добавить рандом на стаж
# добавить действия с игроком
# добавить переролл карточки

if __name__ == "__main__":
    game = Game()
    game.start_game()
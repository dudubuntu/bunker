import os
import pathlib

APP_ROOT = pathlib.Path(__file__).parent

APP_CONFIG = {
    'POSTGRES_DB': os.environ.get('POSTGRES_DB'),
    'POSTGRES_USER': os.environ.get('POSTGRES_USER'),
    'POSTGRES_PASSWORD': os.environ.get('POSTGRES_PASSWORD'),   
    'POSTGRES_HOST': os.environ.get('POSTGRES_HOST'),   
    'POSTGRES_PORT': os.environ.get('POSTGRES_PORT'),
    'TOKEN_EXPIRED_SECONDS': 172800,
    'TOKEN_APP_KEY': os.environ.get('TOKEN_APP_KEY'),
    'APP_ROOT': APP_ROOT,
    'LOG_LEVEL': os.environ.get('LOG_LEVEL'),
    'LOG_FILENAME': os.environ.get('LOG_FILENAME'),
    'LOG_FILEPATH': os.environ.get('LOG_FILEPATH'),
    
    'GAME_MIN_PLAYERS_QUANTITY': 4,
    'GAME_CHARS_QUANTITY': 11,  #Общее количество доступных характеристик: роствес, пол, возрастстаж, ...
}
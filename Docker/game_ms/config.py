import os

APP_CONFIG = {
    'POSTGRES_DB': os.environ.get('POSTGRES_DB'),
    'POSTGRES_USER': os.environ.get('POSTGRES_USER'),
    'POSTGRES_PASSWORD': os.environ.get('POSTGRES_PASSWORD'),   
    'POSTGRES_HOST': os.environ.get('POSTGRES_HOST'),   
    'POSTGRES_PORT': os.environ.get('POSTGRES_PORT'),
    'TOKEN_EXPIRED_SECONDS': 172800,
    'TOKEN_APP_KEY': os.environ.get('TOKEN_APP_KEY'),
}
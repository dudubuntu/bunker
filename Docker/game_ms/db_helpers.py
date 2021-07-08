from aiopg.sa import create_engine


async def init_pg(app):
    config = app['config']

    engine = await create_engine(
        database = config['POSTGRES_DB'],
        user = config['POSTGRES_USER'],
        password = config['POSTGRES_PASSWORD'],
        host = config['POSTGRES_HOST'],
        port = config['POSTGRES_PORT'],
        echo = True,
    )

    app['db'] = engine


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()
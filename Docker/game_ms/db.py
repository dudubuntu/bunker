from sqlalchemy.types import TypeDecorator
from sqlalchemy import Table, MetaData, Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


ROOM_STATES = {
    'waiting': 'waiting',
    'opening': 'opening',
    'voting': 'voting',
    'finished': 'finished',
}

ROOMUSER_STATES = {
    'in_game': 'in_game',
    'kicked': 'kicked',
}

ROOMVOTE_STATES = {
    'waiting_first_time': 'waiting_first_time',
    'first_time_done': 'first_time_done',
    'waiting_second_time': 'waiting_second_time',
    'done': 'done',
}


class Choices(TypeDecorator):
    impl = String

    cache_ok = True

    def __init__(self, choices):
        self.choices = tuple(choices)
        self.internal_only = True


Base = declarative_base()
meta = MetaData()


class User(Base):
    __tablename__ = 'auth_user'

    id = Column('id', Integer(), primary_key=True)
    password = Column('password', String(128))
    last_login = Column('last_login', DateTime(True))
    is_superuser = Column('is_superuser', Boolean())
    username = Column('username', String(150))
    first_name = Column('first_name', String(150))
    last_name = Column('last_name', String(150))
    email = Column('email', String(254))
    is_staff = Column('is_staff', Boolean())
    is_active = Column('is_active', Boolean())
    date_joined = Column('date_joined', DateTime(True))


class Player(Base):
    __tablename__ = 'web_player'
    
    id = Column('id', Integer(), primary_key=True)
    room_username = Column('room_username', String(100))
    user_id = Column('user_id', ForeignKey('auth_user.id')),
    # user_id = relationship('User', backref='player', lazy='dinamic', primaryjoin='User.id == Player.user_id')


class Room(Base):
    __tablename__ = 'web_room'
    
    id = Column('id', Integer(), primary_key=True)
    initiator = Column('initiator', String(100))
    # Column('state', Choices(ROOM_STATES))
    state = Column('state', String())
    turn = Column('turn', Integer())
    lap = Column('lap', Integer())
    quantity_players = Column('quantity_players', Integer())
    created = Column('created', DateTime(True))
    updated = Column('updated', DateTime(True))
    closed = Column('closed', DateTime(True))


class RoomUser(Base):
    __tablename__ = 'web_roomuser'

    id = Column('id', Integer(), primary_key=True)
    username = Column('username', String(100))
    player_number = Column('player_number', Integer())
    info = Column('info', JSON())
    opened = Column('opened', String(1000))
    state = Column('state', String(100))
    card_opened_numbers = Column('card_opened_numbers', String(100))
    room_id = Column('room_id', ForeignKey('web_room.id'))
    user_id = Column('user_id', ForeignKey('auth_user.id'))


class RoomVote(Base):
    __tablename__ = 'web_roomvote'

    id = Column('id', Integer(), primary_key=True)
    vote_lap = Column('vote_lap', Integer())
    state = Column('state', String(100))
    extra = Column('extra', JSON())
    room_id = Column('room_id', ForeignKey('web_room.id'))
from django.contrib.auth.models import User

from django.db import models
from django.urls import reverse


def autoincrement_id():
    largest = Room.objects.all().order_by('id').last()
    if not largest:
        return 1000
    else:
        return largest.id + 1


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player')
    rooms = models.ManyToManyField('Room', related_name='players')
    room_username = models.CharField(max_length=100)
    # configs = models.JSONField()
    friends = models.ManyToManyField('self', symmetrical=True)

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse('web:profile', kwargs={"slug": self.user.username})


class Room(models.Model):
    STATES = (
        ('waiting', 'waiting'),
        ('opening', 'opening'),
        ('voting', 'voting'),
        ('finished', 'finished'),
    )
    id = models.PositiveIntegerField(primary_key=True, default=autoincrement_id)
    # password
    initiator = models.CharField(max_length=100)
    state = models.CharField(max_length=100, choices=STATES)
    turn = models.PositiveSmallIntegerField(default=1)
    lap = models.PositiveSmallIntegerField(default=1)
    quantity_players = models.PositiveSmallIntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    closed = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.id}'

    def get_absolute_url(self):
        return reverse('web:room', kwargs={'id': self.id})


class RoomUser(models.Model):
    STATES = (
        ('in_game', 'in_game'),
        ('kicked', 'kicked'),
    )
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='room_users')
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='room_user')
    username = models.CharField(max_length=100)
    player_number = models.PositiveSmallIntegerField()
    info = models.JSONField()
    opened = models.CharField(max_length=1000)
    state = models.CharField(max_length=100, choices=STATES)
    card_opened_numbers = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.username}-room{self.room_id}'


class RoomVote(models.Model):
    STATES = (
        ('waiting_first_time', 'waiting_first_time'),
        ('first_time_done', 'first_time_done'),
        ('waiting_second_time', 'waiting_second_time'),
        ('done', 'done'),
    )
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='votes')
    vote_lap = models.PositiveSmallIntegerField(default=1)
    state = models.CharField(max_length=100, choices=STATES)
    extra = models.JSONField()

    def __str__(self):
        return f'{self.room_id}-lap{self.room.id}'
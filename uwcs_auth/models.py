from django.contrib.auth.models import User

from django.db import models


class WarwickGGUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    uni_id = models.CharField(max_length=11)
    nickname = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f'{self.uni_id} - {self.nickname if self.nickname else "no nickname"} for user {self.user.id}'

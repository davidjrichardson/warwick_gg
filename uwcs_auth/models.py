from django.contrib.auth.models import User

from django.db import models


class WarwickGGUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    uni_id = models.CharField(max_length=11)
    nickname = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return '{uni_id} - {nick} for user {id}'.format(uni_id=self.uni_id,
                                                        nick=self.nickname if self.nickname else "no nickname",
                                                        id=self.user.id)

    def long_name(self):
        if self.nickname.strip():
            return self.nickname.strip()
        else:
            return self.user.get_full_name()

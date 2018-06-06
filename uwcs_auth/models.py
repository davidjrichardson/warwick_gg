from django.contrib.auth.models import User

from django.db import models
from django.utils import timezone


class WarwickGGUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    uni_id = models.CharField(max_length=11)
    nickname = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return '{uni_id} - {nick} for user {id}'.format(uni_id=self.uni_id,
                                                        nick=self.nickname if self.nickname else "no nickname",
                                                        id=self.user.id)

    @property
    def long_name(self):
        if self.nickname.strip():
            return self.nickname.strip()
        else:
            return self.user.get_full_name()

    @property
    def is_fresher(self):
        start_year = self.uni_id[:2]

        # If we're in the summer months then nobody is a fresher
        if timezone.now().month in range(7, 9):
            return False
        # If we're in the autumn term
        elif timezone.now().month in range(9, 13):
            return start_year == str(timezone.now().year)[2:]
        # Otherwise we're in winter/spring time and we need to subtract a year
        else:
            return start_year == str(timezone.now().year - 1)[2:]


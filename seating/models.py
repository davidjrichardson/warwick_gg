from django.conf import settings
from django.db import models
from django.utils import timezone

from events.models import Event


class RevisionManager(models.Manager):
    def for_event(self, e):
        return self.filter(event=e).order_by('-number')


class SeatingRevision(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    number = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    objects = RevisionManager()

    def prev(self):
        return SeatingRevision.objects.get(event=self.event, number=self.number - 1)

    def added(self):
        """
        People who were added to the seating plan in the current
        revision.
        Returns an iterable of Seating Objects
        """
        try:
            return self.seating_set.exclude(user__in=self.prev().users())
        except SeatingRevision.DoesNotExist:
            return self.seating_set.all()

    def removed(self):
        try:
            return self.prev().seating_set.exclude(user__in=self.users())
        except SeatingRevision.DoesNotExist:
            return self.seating_set.none()

    def moved(self):
        try:
            current = self.seating_set.filter(user__in=self.prev().users()).order_by('user')
            previous = self.prev().seating_set.filter(user__in=self.users()).order_by('user')
            return filter(lambda curr, prev: curr.col != prev.col or curr.row != prev.row, zip(current, previous))
        except SeatingRevision.DoesNotExist:
            return self.seating_set.none()

    class Meta:
        unique_together = ('event', 'number')
        ordering = ['-number']


class SeatingManager(models.Manager):
    def for_event(self, e):
        """
        Get all the seatings for every revision for a specific event
        """
        return self.filter(revision__event=e)


class Seating(models.Model):
    reserved = models.BooleanField(default=False)
    revision = models.ForeignKey(SeatingRevision, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    table = models.IntegerField()
    seat = models.IntegerField()

    objects = SeatingManager()

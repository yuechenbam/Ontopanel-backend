from django.db import models

from django.utils import timezone
from django.contrib.auth.models import User


class Onto(models.Model):
    title = models.CharField(max_length=255)

    onto_source = models.CharField(max_length=255)
    onto_file = models.TextField()

    onto_table = models.JSONField()
    date_created = models.DateField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('title',)
        unique_together = ("author", "title")

    def __str__(self):
        return self.title

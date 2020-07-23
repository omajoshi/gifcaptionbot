from django.db import models
from django.conf import settings
import os

# Create your models here.

class Movie(models.Model):
    srt = models.FileField(blank=True, upload_to=lambda i,filename: f"subtitles/{i.name}.{filename.split('.')[-1]}")
    movie = models.FileField(blank=True, upload_to=lambda i,filename: f"movies/{i.name}.{filename.split('.')[-1]}")
    name = models.CharField(max_length=100, blank=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name

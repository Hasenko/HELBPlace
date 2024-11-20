from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse

# Create your models here.
"""
class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self): # toString()
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})
"""
class Canvas(models.Model):

    title = models.CharField(max_length=100)
    width = models.PositiveIntegerField(default=100)
    height = models.PositiveIntegerField(default=100)
    time_to_wait = models.PositiveIntegerField(default=3)

    content = models.TextField(default='blank')

    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def get_pixel_list(content):
        pixel_list = []
        i = 0
        pixel = ""
        for letter in content:
            if i%7 == 0 and i != 0:
                pixel_list.append(pixel)
                pixel = ""

            pixel += letter
            i += 1

        pixel_list.append(pixel)

        return pixel_list

    def change_pixel(self, content, pixel_index: int, new_color: str):
        pixel_list = self.get_pixel_list(content)
        pixel_list[pixel_index] = new_color

        return ''.join(pixel_list)

    def __str__(self): # toString()
        return self.title

    def get_absolute_url(self):
        return reverse('canvas-detail', kwargs={'pk': self.pk})
    
    def save(self):
        def blank(width, height):
            return "#FFFFFF" * width * height

        if self.content == "blank":
            self.content = blank(self.width, self.height)
        return super().save()
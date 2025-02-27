from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Canvas, CanvasStatistics

@receiver(post_save, sender=Canvas)
def create_canvas_statistics(sender, instance, created, **kwargs):
    if created:
        CanvasStatistics.objects.create(canvas=instance)
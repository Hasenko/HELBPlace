from django.contrib import admin
from .models import Canvas, Contribution, CanvasStatistics

# Register your models here.
admin.site.register(Canvas)
admin.site.register(Contribution)
admin.site.register(CanvasStatistics)
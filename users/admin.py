from django.contrib import admin
from .models import Profile, UserStatistics

# Register your models here.

admin.site.register(Profile)
admin.site.register(UserStatistics)
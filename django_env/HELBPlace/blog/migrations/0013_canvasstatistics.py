# Generated by Django 4.2.16 on 2024-12-10 14:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_alter_canvas_height_alter_canvas_time_to_wait_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CanvasStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contributions_day', models.JSONField(default=dict)),
                ('canvas', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.canvas')),
            ],
        ),
    ]

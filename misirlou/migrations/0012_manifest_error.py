# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-03 18:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('misirlou', '0011_auto_20160603_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='manifest',
            name='error',
            field=models.IntegerField(default=0),
        ),
    ]

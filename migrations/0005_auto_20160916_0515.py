# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-16 05:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grain', '0004_auto_20160914_0723'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meal',
            name='consumer',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='grain.Consumer'),
            preserve_default=False,
        ),
    ]

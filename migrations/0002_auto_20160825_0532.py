# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-25 05:32
# flake8: noqa
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('grain', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Consumer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('actual_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='grain.UserProfile')),
            ],
        ),
        migrations.AlterField(
            model_name='unit',
            name='short',
            field=models.CharField(max_length=8, verbose_name='abbreviation'),
        ),
        migrations.AlterField(
            model_name='unit',
            name='verbose',
            field=models.CharField(max_length=20, verbose_name='name (singular)'),
        ),
        migrations.AddField(
            model_name='meal',
            name='consumer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='grain.Consumer'),
        ),
    ]

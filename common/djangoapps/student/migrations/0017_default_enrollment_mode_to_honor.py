# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-09-25 17:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0016_coursenrollment_course_on_delete_do_nothing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseenrollment',
            name='mode',
            field=models.CharField(default='honor', max_length=100),
        ),
    ]

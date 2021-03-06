# Generated by Django 2.0.6 on 2018-10-04 13:21

import datetime
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('intranet', '0005_auto_20181003_1021'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='nots_view',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='adhesion',
            name='created',
            field=models.DateField(default=datetime.date(2018, 10, 4), verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='adhesion',
            name='end',
            field=models.DateField(default=datetime.date(2019, 10, 4), verbose_name='date de fin'),
        ),
        migrations.AlterField(
            model_name='attestation',
            name='created',
            field=models.DateField(default=datetime.date(2018, 10, 4), verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='attestation',
            name='last',
            field=models.DateField(default=datetime.date(2019, 10, 4), verbose_name="date d'échéance"),
        ),
        migrations.AlterField(
            model_name='condition',
            name='start',
            field=models.DateField(default=datetime.date(2018, 10, 5), verbose_name='Début'),
        ),
        migrations.AlterField(
            model_name='examen',
            name='last',
            field=models.DateField(default=datetime.date(2018, 11, 3), verbose_name='Clôture des inscriptions'),
        ),
        migrations.AlterField(
            model_name='facture',
            name='created',
            field=models.DateField(default=datetime.date(2018, 10, 4), verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='facture',
            name='last',
            field=models.DateField(default=datetime.date(2018, 10, 11), verbose_name="date d'échéance"),
        ),
        migrations.AlterField(
            model_name='prix',
            name='start',
            field=models.DateField(default=datetime.date(2018, 10, 5), verbose_name='Début'),
        ),
        migrations.AlterField(
            model_name='stats',
            name='date',
            field=models.DateField(default=datetime.date(2018, 10, 4)),
        ),
    ]

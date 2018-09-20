# Generated by Django 2.0.6 on 2018-09-14 11:58

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intranet', '0007_auto_20180913_0956'),
    ]

    operations = [
        migrations.AddField(
            model_name='prix',
            name='adhesion_prof',
            field=models.FloatField(blank=True, default=15.83, max_length=5),
        ),
        migrations.AddField(
            model_name='prix',
            name='adhesion_reduc',
            field=models.FloatField(default=60, max_length=5),
        ),
        migrations.AddField(
            model_name='prix',
            name='cours_premium',
            field=models.FloatField(blank=True, default=51.0, max_length=5),
        ),
        migrations.AlterField(
            model_name='attestation',
            name='created',
            field=models.DateField(default=datetime.date(2018, 9, 14), verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='attestation',
            name='last',
            field=models.DateField(default=datetime.date(2019, 9, 14), verbose_name="date d'échéance"),
        ),
        migrations.AlterField(
            model_name='facture',
            name='created',
            field=models.DateField(default=datetime.date(2018, 9, 14), verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='facture',
            name='last',
            field=models.DateField(default=datetime.date(2018, 9, 21), verbose_name="date d'échéance"),
        ),
        migrations.AlterField(
            model_name='prix',
            name='adhesion',
            field=models.FloatField(default=66.67, max_length=5),
        ),
        migrations.AlterField(
            model_name='prix',
            name='commission',
            field=models.FloatField(default=0.83, max_length=5),
        ),
        migrations.AlterField(
            model_name='prix',
            name='cours',
            field=models.FloatField(default=41.0, max_length=5),
        ),
        migrations.AlterField(
            model_name='prix',
            name='frais_gestion',
            field=models.FloatField(default=7.5, max_length=5),
        ),
        migrations.AlterField(
            model_name='prix',
            name='start',
            field=models.DateField(default=datetime.date(2018, 9, 15), verbose_name='Début'),
        ),
        migrations.AlterField(
            model_name='prix',
            name='tva',
            field=models.FloatField(default=20.0, max_length=5),
        ),
        migrations.AlterField(
            model_name='stats',
            name='date',
            field=models.DateField(default=datetime.date(2018, 9, 14)),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='is_premium',
            field=models.BooleanField(default=False, help_text="Permet d'annuler un cours à la dernière minute, les cours sont majorés de 10€"),
        ),
    ]
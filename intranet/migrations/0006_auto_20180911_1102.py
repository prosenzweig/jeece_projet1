# Generated by Django 2.0.6 on 2018-09-11 09:02

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intranet', '0005_auto_20180910_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='stats',
            field=models.CharField(blank=True, choices=[('A', 'Moteur de rechercheGoogle'), ('B', 'Facebook'), ('C', 'Autre source internet'), ('D', 'Annuaire(pages jaunes...)'), ('E', 'Nebout & Hamm'), ('F', 'Falado'), ('G', 'Connaissance(famille, amis...)')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='attestation',
            name='created',
            field=models.DateField(default=datetime.date(2018, 9, 11), verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='attestation',
            name='last',
            field=models.DateField(default=datetime.date(2019, 9, 11), verbose_name="date d'échéance"),
        ),
        migrations.AlterField(
            model_name='facture',
            name='created',
            field=models.DateField(default=datetime.date(2018, 9, 11), verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='facture',
            name='last',
            field=models.DateField(default=datetime.date(2018, 9, 18), verbose_name="date d'échéance"),
        ),
        migrations.AlterField(
            model_name='prix',
            name='start',
            field=models.DateField(default=datetime.date(2018, 9, 12), verbose_name='Début'),
        ),
        migrations.AlterField(
            model_name='stats',
            name='date',
            field=models.DateField(default=datetime.date(2018, 9, 11)),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='nb_facture',
            field=models.IntegerField(default=1),
        ),
    ]

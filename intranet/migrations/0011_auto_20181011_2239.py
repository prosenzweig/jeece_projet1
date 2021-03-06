# Generated by Django 2.0.6 on 2018-10-11 20:39

from django.db import migrations, models
import django.utils.timezone
import intranet.models


class Migration(migrations.Migration):

    dependencies = [
        ('intranet', '0010_auto_20181010_1609'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adhesion',
            name='created',
            field=models.DateField(default=django.utils.timezone.now, verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='adhesion',
            name='end',
            field=models.DateField(default=intranet.models.one_more_year, verbose_name='date de fin'),
        ),
        migrations.AlterField(
            model_name='attestation',
            name='created',
            field=models.DateField(default=django.utils.timezone.now, verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='attestation',
            name='last',
            field=models.DateField(default=intranet.models.one_more_year, verbose_name="date d'échéance"),
        ),
        migrations.AlterField(
            model_name='condition',
            name='start',
            field=models.DateField(default=intranet.models.one_more_day, verbose_name='Début'),
        ),
        migrations.AlterField(
            model_name='examen',
            name='last',
            field=models.DateField(default=intranet.models.thirty_more_days, verbose_name='Clôture des inscriptions'),
        ),
        migrations.AlterField(
            model_name='facture',
            name='created',
            field=models.DateField(default=django.utils.timezone.now, verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='facture',
            name='last',
            field=models.DateField(default=intranet.models.seven_more_days, verbose_name="date d'échéance"),
        ),
        migrations.AlterField(
            model_name='prix',
            name='start',
            field=models.DateField(default=intranet.models.one_more_day, verbose_name='Début'),
        ),
        migrations.AlterField(
            model_name='stats',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]

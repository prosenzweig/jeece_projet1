# Generated by Django 2.0.6 on 2018-09-27 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intranet', '0003_userprofile_nb_adh'),
    ]

    operations = [
        migrations.AddField(
            model_name='attestation',
            name='nb_adh',
            field=models.IntegerField(default=1),
        ),
    ]
# Generated by Django 2.2.4 on 2019-08-08 18:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20190808_1540'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='estado',
            options={'ordering': ['pais', 'nome'], 'verbose_name': 'Estado', 'verbose_name_plural': 'Estados'},
        ),
    ]

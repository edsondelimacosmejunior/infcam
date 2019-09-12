# Generated by Django 2.2.4 on 2019-08-08 19:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20190808_1544'),
    ]

    operations = [
        migrations.AlterField(
            model_name='empresa',
            name='slogan',
            field=models.CharField(blank=True, max_length=200, verbose_name='Slogan'),
        ),
        migrations.AlterField(
            model_name='endereco',
            name='pessoa',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Pessoa', verbose_name='Pessoa'),
        ),
        migrations.AlterField(
            model_name='pessoa',
            name='foto',
            field=models.ImageField(blank=True, upload_to='', verbose_name='Foto'),
        ),
    ]

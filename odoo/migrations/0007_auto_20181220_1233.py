# Generated by Django 2.1.3 on 2018-12-20 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('odoo', '0006_odooparceiro_tipo_cliente'),
    ]

    operations = [
        migrations.AlterField(
            model_name='odooparceiro',
            name='tipo_cliente',
            field=models.CharField(choices=[('BL', 'Banda Larga'), ('CORP', 'Corporativo'), ('LIC', 'Licitado')], default='BL', max_length=4, verbose_name='Tipo do Cliente'),
        ),
    ]

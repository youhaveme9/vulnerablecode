# Generated by Django 4.0.3 on 2022-04-15 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vulnerabilities', '0008_alter_vulnerabilityseverity_scoring_system'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advisory',
            name='summary',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='advisory',
            name='unique_content_id',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='vulnerability',
            name='summary',
            field=models.TextField(blank=True, help_text='Summary of the vulnerability'),
        ),
        migrations.AlterField(
            model_name='vulnerabilityreference',
            name='reference_id',
            field=models.CharField(blank=True, help_text='An optional reference ID, such as DSA-4465-1 when available', max_length=200),
        ),
    ]
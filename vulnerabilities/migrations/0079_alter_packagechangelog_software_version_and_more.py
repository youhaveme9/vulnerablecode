# Generated by Django 4.2.16 on 2024-11-14 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vulnerabilities", "0078_alter_vulnerabilityseverity_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="packagechangelog",
            name="software_version",
            field=models.CharField(
                default="34.3.0",
                help_text="Version of the software at the time of change",
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="vulnerabilitychangelog",
            name="software_version",
            field=models.CharField(
                default="34.3.0",
                help_text="Version of the software at the time of change",
                max_length=100,
            ),
        ),
    ]
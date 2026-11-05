from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesetting",
            name="youtube_url",
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name="aboutfeature",
            name="text",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="processstep",
            name="icon",
            field=models.CharField(
                choices=[
                    ("clipboard", "Clipboard"),
                    ("hand", "Hand"),
                    ("wand", "Wand"),
                    ("check", "Check"),
                ],
                default="clipboard",
                max_length=20,
            ),
        ),
    ]

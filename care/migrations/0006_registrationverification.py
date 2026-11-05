from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0005_booking_payment"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistrationVerification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("full_name", models.CharField(max_length=80)),
                ("phone", models.CharField(max_length=20)),
                ("password_hash", models.CharField(max_length=128)),
                ("otp_hash", models.CharField(max_length=128)),
                ("expires_at", models.DateTimeField()),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Registration verification",
                "verbose_name_plural": "Registration verifications",
            },
        ),
    ]

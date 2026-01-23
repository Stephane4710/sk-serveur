from django.apps import AppConfig
import os

class ServeurConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'serveur'

    def ready(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if username and password:
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )

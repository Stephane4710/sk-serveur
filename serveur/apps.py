from django.apps import AppConfig
from django.contrib.auth import get_user_model
import os


class ServeurConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'serveur'

    def ready(self):
        User = get_user_model()

        username = os.environ.get("sk")
        email = os.environ.get("lesaints969@gmail.com")
        password = os.environ.get("Dieu4710")

        if not username or not password:
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )

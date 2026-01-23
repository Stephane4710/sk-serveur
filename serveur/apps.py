from django.apps import AppConfig
import os

class ServeurConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "serveur"

    def ready(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = os.environ.get("sk")
        email = os.environ.get("lesaints969@gmail.com")
        password = os.environ.get("Dieu4710")

        if username and password:
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )

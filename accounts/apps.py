# from django.apps import AppConfig


# class AccountsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'accounts'

from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from .management.commands.createsuperuser import Command
        post_migrate.connect(create_superuser, sender=self)

def create_superuser(sender, **kwargs):
    from django.contrib.auth import get_user_model
    import os

    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser(
            username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'),
            email=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
            password=os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin'),
            is_general=True,
            is_admin=True,
        )
        print('Superuser created successfully.')
    else:
        print('Superuser already exists.')



from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = 'Create a superuser if none exists'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'),
                email=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
                password=os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin'),
                is_general=True,
                is_admin=True,
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully.'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser already exists.'))

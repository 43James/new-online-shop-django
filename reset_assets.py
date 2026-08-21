import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from assets.models import AssetItem, AssetCode

AssetItem.objects.all().delete()
AssetCode.objects.all().delete()
print("All assets cleared.")

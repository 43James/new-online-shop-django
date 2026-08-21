import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_shop.settings')
django.setup()

from assets.models import AssetItem, AssetCode, AssetOwnership, AssetCheck, AssetTransferItem, AssetTransferRequest
from django.db import connection

print("Deleting all AssetItem and AssetCode...")
AssetItem.objects.all().delete()
AssetCode.objects.all().delete()
AssetTransferRequest.objects.all().delete()

with connection.cursor() as cursor:
    cursor.execute("ALTER TABLE assets_assetitem AUTO_INCREMENT = 1;")
    cursor.execute("ALTER TABLE assets_assetcode AUTO_INCREMENT = 1;")
    cursor.execute("ALTER TABLE assets_assetownership AUTO_INCREMENT = 1;")
    cursor.execute("ALTER TABLE assets_assetcheck AUTO_INCREMENT = 1;")
    cursor.execute("ALTER TABLE assets_assettransferitem AUTO_INCREMENT = 1;")
    cursor.execute("ALTER TABLE assets_assettransferrequest AUTO_INCREMENT = 1;")

print("Data cleared and auto_increment reset.")

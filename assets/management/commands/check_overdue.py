from django.core.management.base import BaseCommand
from django.utils import timezone
from assets.models import OrderAssetLoan

class Command(BaseCommand):
    help = 'Checks for overdue asset loans and updates their status.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting to check for overdue loans...")

        # ค้นหาออเดอร์ที่สถานะเข้าข่ายและเลยกำหนดคืน
        overdue_orders = OrderAssetLoan.objects.filter(
            status__in=['pending', 'approved', 'borrowed', 'returned_pending'],
            date_due__lt=timezone.now()
        )

        updated_count = overdue_orders.update(status='overdue')

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} overdue orders.'))
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_shop.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from accounts.models import PortalApp

# สร้างข้อมูลเริ่มต้น
apps_data = [
    {
        'code': 'SIP-01',
        'title': 'ระบบเบิกวัสดุ',
        'category': 'admin',
        'description': 'ระบบสำหรับทำรายการเบิก-จ่ายวัสดุสิ้นเปลือง',
        'url': 'http://127.0.0.1:8002/login/?next=/shop/home_page/',
        'icon': 'fa-box-open',
        'icon_color': 'text-sky-600 bg-sky-50',
        'is_favorite': True,
        'order': 1,
    },
    {
        'code': 'SIP-02',
        'title': 'ระบบยืมครุภัณฑ์',
        'category': 'admin',
        'description': 'ระบบบริหารจัดการยืม-คืนครุภัณฑ์และตรวจสอบสถานะ',
        'url': 'http://127.0.0.1:8002/login/?next=/assets/calendar/',
        'icon': 'fa-boxes-stacked',
        'icon_color': 'text-emerald-600 bg-emerald-50',
        'is_favorite': True,
        'order': 2,
    },
]

for data in apps_data:
    app, created = PortalApp.objects.get_or_create(
        code=data['code'],
        defaults=data
    )
    if created:
        print(f"[OK] Created [{app.code}] {app.title}")
    else:
        print(f"[SKIP] Exists [{app.code}] {app.title}")

print(f"Total apps in Portal: {PortalApp.objects.count()}")

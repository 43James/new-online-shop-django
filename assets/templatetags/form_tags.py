from django import template
from assets.models import AssetTransferRequest, OrderAssetLoan

register = template.Library()

@register.simple_tag
def get_user_active_loan_count(user):
    """
    คืนค่าจำนวนรายการคำร้องขอยืมครุภัณฑ์ ของผู้ใช้ปัจจุบัน ที่สถานะกำลังใช้งาน (รออนุมัติ, กำลังยืม, เกินกำหนด, รอตรวจสอบการคืน)
    """
    if not user.is_authenticated:
        return 0
    return OrderAssetLoan.objects.filter(
        user=user,
        status__in=['pending', 'approved', 'overdue', 'returned_pending']
    ).count()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.simple_tag
def get_pending_transfer_count():
    """
    คืนค่าจำนวนรายการคำร้องขอเคลื่อนย้าย/ส่งคืน ที่สถานะกำลังรอพิจารณา
    """
    return AssetTransferRequest.objects.filter(
        status__in=['PENDING_HEAD', 'PENDING_DIRECTOR', 'PENDING_ACTION']
    ).count()

@register.simple_tag
def get_user_pending_transfer_count(user):
    """
    คืนค่าจำนวนรายการคำร้องขอเคลื่อนย้าย/ส่งคืน ของผู้ใช้ปัจจุบัน ที่สถานะกำลังรอพิจารณา
    """
    if not user.is_authenticated:
        return 0
    return AssetTransferRequest.objects.filter(
        requester=user,
        status__in=['PENDING_HEAD', 'PENDING_DIRECTOR', 'PENDING_ACTION']
    ).count()

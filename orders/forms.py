from django import forms
from django.forms import ModelForm

from orders.models import Issuing, Order, OutOfStockNotification

class UserApproveForm(ModelForm):
    class Meta:
        model = Order
        fields = ('confirm', 'name_sign', 'date_received')
        # exclude = ('user', 'datecreated')

# class managerApproveForm(ModelForm):
#     class Meta:
#         model = Order
#         fields = ('pay_item', 'name_pay', 'surname_pay')
        # exclude = ('user', 'datecreated')

# class ApprovereportForm(forms.ModelForm):
#     class Meta:
#         model = Approvereport
#         fields = [
#             'month_report', 'name_sign1', 'surname_sign1', 'position1',
#             'name_sign2', 'surname_sign2', 'position2', 'approve',
#             'name_approve', 'surname_approve', 'position3', 'other'
#         ]


from django import forms

class UserOutOfStockNotificationForm(forms.ModelForm):
    class Meta:
        model = OutOfStockNotification
        fields = ['product', 'quantity_requested', 'note']
        



from django import forms
from django.forms import ModelForm

from orders.models import Issuing, Order

class UserApproveForm(ModelForm):
    class Meta:
        model = Order
        fields = ('confirm', 'name_sign', 'date_received')
        # exclude = ('user', 'datecreated')
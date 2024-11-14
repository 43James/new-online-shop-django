import datetime
from django import forms
from django.forms import ModelForm

from accounts.models import WorkGroup
from shop.models import Product, Category, Receiving, Subcategory, Suppliers
from orders.models import Issuing, Order


class MonthYearForm(forms.Form):
    MONTH_CHOICES = [
        ('มกราคม', 'มกราคม'), ('กุมภาพันธ์', 'กุมภาพันธ์'), ('มีนาคม', 'มีนาคม'), ('เมษายน', 'เมษายน'),
        ('พฤษภาคม', 'พฤษภาคม'), ('มิถุนายน', 'มิถุนายน'), ('กรกฎาคม', 'กรกฎาคม'), ('สิงหาคม', 'สิงหาคม'),
        ('กันยายน', 'กันยายน'), ('ตุลาคม', 'ตุลาคม'), ('พฤศจิกายน', 'พฤศจิกายน'), ('ธันวาคม', 'ธันวาคม'),
    ]
    YEAR_CHOICES = [(year, year) for year in range(2563, 2563 + 10)]  # ปี 2563 - 2572

    month = forms.ChoiceField(choices=MONTH_CHOICES, label='เดือน', required=True)
    year = forms.ChoiceField(choices=YEAR_CHOICES, label='ปี', required=True)

class UploadFileForm(forms.Form):
    file = forms.FileField(label='เลือกไฟล์ Excel')


class AddProductForm(ModelForm):
    # category = forms.ModelChoiceField(queryset=Subcategory.objects.all(), label='หมวดหมู๋', empty_label='เลือก..')
    category = forms.ModelChoiceField(
        queryset=Subcategory.objects.all(),
        label='หมวดหมู๋',
        empty_label='เลือก..',
        widget=forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true'})
    )

    class Meta:
        model = Product
        fields = ['category', 'image', 'product_id', 'product_name', 'unit', 'description']

    def __init__(self, *args, **kwargs):
        super(AddProductForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class AddSuppliersForm(ModelForm):
    class Meta:
        model = Suppliers
        fields = ['supname','taxnumber', 'contactname', 'phone', 'address']

    def __init__(self, *args, **kwargs):
        super(AddSuppliersForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class AddReceivingForm(ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label='สินค้า', empty_label='เลือก..')
    suppliers = forms.ModelChoiceField(queryset=Suppliers.objects.all(), label='ซัพพลายเออร์', empty_label='เลือก..')

    class Meta:
        model = Receiving
        fields = ['product', 'suppliers', 'file', 'date_received', 'quantityreceived', 'quantity', 'unitprice', 'note']

    def __init__(self, *args, **kwargs):
        super(AddReceivingForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            

        # self.fields['product'].queryset = Product.objects.all().values_list('product_name', flat=True)
        # self.fields['suppliers'].queryset = Suppliers.objects.all().values_list('supname', flat=True)

class ReceivingForm(forms.ModelForm):
    class Meta:
        model = Receiving
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ReceivingForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class WorkGroupForm(forms.ModelForm):
    class Meta:
        model = WorkGroup
        fields = ['work_group']

    def __init__(self, *args, **kwargs):
        super(WorkGroupForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class EditWorkGroupForm(ModelForm):
    class Meta:
        model = WorkGroup
        fields = ['work_group']

    def __init__(self, *args, **kwargs):
        super(EditWorkGroupForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        

class AddCategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name_cate']

    def __init__(self, *args, **kwargs):
        super(AddCategoryForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class AddSubcategoryForm(ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), label='หมวดหมู่หลัก', empty_label='เลือก..')
    class Meta:
        model = Subcategory
        fields = ['name_sub', 'category']
    
    def __init__(self, *args, **kwargs):
        super(AddSubcategoryForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
    
    # def __init__(self, *args, **kwargs):
    #     super(AddSubcategoryForm, self).__init__(*args, **kwargs)
    #     self.fields['name'].widget.attrs['class'] = 'form-control'
    #     self.fields['category'].widget.attrs['class'] = 'form-control'


class EditProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'image', 'product_id', 'product_name', 'quantityinstock', 'unit', 'description']

    def __init__(self, *args, **kwargs):
        super(EditProductForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['style'] = 'color: rgb(8, 0, 255);'
            

class EditSuppliersForm(ModelForm):
    class Meta:
        model = Suppliers
        fields = ['supname','taxnumber', 'contactname', 'phone', 'address']

    def __init__(self, *args, **kwargs):
        super(EditSuppliersForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class ApproveForm(ModelForm):
    class Meta:
        model = Order
        fields = ('status', 'date_receive', 'other')
        # exclude = ('user', 'datecreated')

class ApprovePayForm(ModelForm):
    class Meta:
        model = Order
        fields = ('pay_item', 'name_pay', 'surname_pay')
        # exclude = ('user', 'datecreated')
    

class EditCategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name_cate']

    def __init__(self, *args, **kwargs):
        super(EditCategoryForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class EditSubcategoryForm(ModelForm):
    class Meta:
        model = Subcategory
        fields = ['name_sub', 'category']

    def __init__(self, *args, **kwargs):
        super(EditSubcategoryForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class RecordMonthlyStockForm(forms.Form):
    confirm = forms.BooleanField(
        label="ยืนยันการบันทึกยอดสินค้าคงเหลือประจำเดือน",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'flexCheckDefault'})
    )


class OrderFilterForm(forms.Form):
    year = forms.ChoiceField(choices=[('', 'เลือกปี')], required=False)
    month = forms.ChoiceField(choices=[('', 'เลือกเดือน')] + [(str(i), str(i)) for i in range(1, 13)], required=False)
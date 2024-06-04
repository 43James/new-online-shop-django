from django import forms
from django.forms import ModelForm

from shop.models import Product, Category, Receiving, Subcategory, Suppliers
from orders.models import Issuing, Order


class AddProductForm(ModelForm):
    category = forms.ModelChoiceField(queryset=Subcategory.objects.all(), label='หมวดหมู๋', empty_label='เลือก..')

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
        fields = ['supname', 'contactname', 'phone', 'address']

    def __init__(self, *args, **kwargs):
        super(AddSuppliersForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class AddReceivingForm(ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label='สินค้า', empty_label='เลือก..')
    suppliers = forms.ModelChoiceField(queryset=Suppliers.objects.all(), label='ซัพพลายเออร์', empty_label='เลือก..')

    class Meta:
        model = Receiving
        fields = ['product', 'suppliers', 'quantityreceived', 'quantity', 'unitprice']

    def __init__(self, *args, **kwargs):
        super(AddReceivingForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            

        # self.fields['product'].queryset = Product.objects.all().values_list('product_name', flat=True)
        # self.fields['suppliers'].queryset = Suppliers.objects.all().values_list('supname', flat=True)


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
        fields = ['category', 'image', 'product_id', 'product_name', 'unit', 'description']

    def __init__(self, *args, **kwargs):
        super(EditProductForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            

class EditSuppliersForm(ModelForm):
    class Meta:
        model = Suppliers
        fields = ['supname', 'contactname', 'phone', 'address']

    def __init__(self, *args, **kwargs):
        super(EditSuppliersForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class ApproveForm(ModelForm):
    class Meta:
        model = Order
        fields = ('status', 'date_receive', 'other')
        exclude = ('user', 'datecreated')


class ReceivingForm(forms.ModelForm):
    class Meta:
        model = Receiving
        fields = '__all__'


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
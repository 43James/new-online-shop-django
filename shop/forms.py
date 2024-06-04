from shop.models import Category, Subcategory

# สร้าง Category
category1 = Category.objects.create(name='Category 1')

# สร้าง Subcategory ที่เชื่อมกับ Category 1
subcategory1 = Subcategory.objects.create(name='Subcategory 1', category=category1)

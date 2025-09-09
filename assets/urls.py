from django.urls import path

from assets import views
# from .views import filter_by_category

app_name = "assets"

urlpatterns = [
	# path('base_sidebar/', views.base, name='base_sidebar'),
    # หน้าแรก
	path('home/', views.home_assets, name='home_assets'),
    # เพิ่ม เช็ค รายการ ครุภัณฑ์
    path('add-asset/', views.add_asset_item, name='add_asset_item'),
    path("check-asset/", views.check_asset, name="check_asset"),
    path("asset-list/", views.asset_list, name="asset_list"),
    path('asset/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('asset/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('asset/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
    # path("asset/check/<int:asset_id>/", views.check_asset, name="check_asset"),

    # เพิ่มผู้ครอบครอง
    # path('ownership-create/', views.create_asset_ownership, name='create_asset_ownership'), 


    # รายการที่ยืม ยืม อนุมัติยืม ยืนยันรับ แจ้งคืน อนุมันิคืน
    path('add-asset-loan/', views.add_asset_item_loan, name='add_asset_item_loan'),
    path("loan-list/", views.loan_list, name="loan_list"),
    path('loan-list/edit/<int:pk>/', views.edit_asset_item_loan, name='edit_asset_item_loan'),
    path('loan-list/delete/<int:pk>/', views.delete_asset_item_loan, name='delete_asset_item_loan'),
    

    # หน้าแสดงรายละเอียดครุภัณฑ์
    path("loan-detail/<int:loan_id>/", views.loan_detail_view, name="loan_detail"),

    # ตะกร้า
    path("loan-cart/", views.loan_cart, name="loan_cart"),

    # ยืนยันการยืมและจอง
    path("confirm-loan/", views.confirm_loan, name="confirm_loan"),
    path('loan-list/reserve/<int:pk>/', views.reserve_asset_item, name='reserve_asset_item'),
    # รายการอนุมัติการยืม
    path("loan-approval-list/", views.loan_approval_list, name="loan_approval_list"),
    path("loan-approval/<int:pk>/", views.loan_approval, name="loan_approval"),
    
    path("approve-return/<int:loan_id>/", views.approve_return, name="approve_return"),
    # path("loan-approval/<int:loan_id>/", views.loan_approval, name="loan_approval"),
    # path("confirm-receipt/<int:loan_id>/", views.confirm_receipt, name="confirm_receipt"),
    # path("return/<int:loan_id>/", views.request_return, name="request_return"),
    # path("approve-return/<int:loan_id>/", views.approve_return, name="approve_return"),

    # รายการแจ้งซ่อม
    # path("repair-report/", views.repair_report, name="repair_report"),

    # หมวดหมู่หลัก
    # path("category-list/", views.asset_list_cate, name="asset_list_cate"),
    # path('add-category/', views.add_category_asset, name='add_category_asset'),
    path('category/list/', views.asset_list_cate, name='asset_list_cate'),
    path('category/add/', views.add_category_asset, name='add_category_asset'),
    path('category/edit/<int:pk>/', views.edit_category_asset, name='edit_category_asset'),
    path('category/delete/<int:pk>/', views.delete_category_asset, name='delete_category_asset'),
    # หมวดหมู่ย่อย,ที่เก็บ
    path('subcategory/list/', views.asset_list_subcate, name='asset_list_subcate'),
    path('subcategory/add/', views.add_subcategory_asset, name='add_subcategory_asset'),
    path('subcategory/edit/<int:pk>/', views.edit_subcategory_asset, name='edit_subcategory_asset'),
    path('subcategory/delete/<int:pk>/', views.delete_subcategory_asset, name='delete_subcategory_asset'),
    # ช่องค้นหา
    # path('category/search/', views.search_category, name='search_category'),
    # path('add-storage/', views.add_storage_location, name='add_storage_location'),

    # ที่เก็บ
    path('storage_location/list/', views.asset_list_storage_location, name='asset_list_storage_location'),
    # path('storage_location/add/', views.add_storage_location_asset, name='add_storage_location_asset'),
    path('storage_location/edit/<int:pk>/', views.edit_storage_location_asset, name='edit_storage_location_asset'),
    path('storage_location/delete/<int:pk>/', views.delete_storage_location_asset, name='delete_storage_location_asset'),

]


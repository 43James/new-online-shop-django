from django.urls import path

from assets import views
# from .views import filter_by_category

app_name = "assets"

urlpatterns = [
	# path('base_sidebar/', views.base, name='base_sidebar'),
	path('assets-home/', views.home_assets, name='home_assets'),
    path('asset-add/', views.add_asset_item, name='add_asset_item'),
    path('ownership-create/', views.create_asset_ownership, name='create_asset_ownership'),
    path("asset-check/", views.check_asset, name="check_asset"),
    path("asset-list/", views.asset_list, name="asset_list"),
    # path("asset/check/<int:asset_id>/", views.check_asset, name="check_asset"),

    # รายการที่ยืม ยืม อนุมัติยืม ยืนยันรับ แจ้งคืน อนุมันิคืน
    path("loan-list/", views.loan_list, name="loan_list"),
    path("request-loan/", views.request_loan, name="request_loan"),
    path("loan-approval/<int:loan_id>/", views.loan_approval, name="loan_approval"),
    path("confirm-receipt/<int:loan_id>/", views.confirm_receipt, name="confirm_receipt"),
    path("return/<int:loan_id>/", views.request_return, name="request_return"),
    path("approve-return/<int:loan_id>/", views.approve_return, name="approve_return"),
]


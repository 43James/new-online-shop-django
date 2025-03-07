from django.urls import path

from dashboard import views


app_name = 'dashboard'


urlpatterns = [
    # path('dashboard_home/', order_by_work_group_year_chart_json, name='order_by_work_group_year_chart_json'),
    path('dashboard_home/', views.dashboard_home, name='dashboard_home'),
    path('dashboard_report/', views.dashboard_report, name='dashboard_report'),
    path('issuing_report/', views.issuing_report, name='issuing_report'),

    path('products/', views.products, name='products'),
    path('add-product/', views.add_product, name='add_product'),
    path('products/delete/<int:id>/', views.delete_product, name='delete_product'),
    path('products-edit/<int:id>/', views.edit_product, name='edit_product'),

    path('orders/', views.orders, name='orders'),
    path('orders_all/', views.orders_all, name='orders_all'),
    path('approve/orders/<int:order_id>/', views.approve_orders, name='approve_orders'),
    path('approve-payitem/<int:order_id>/', views.approve_pay, name='approve_pay'),
    path('orders_detail/<int:id>/', views.order_detail, name='order_detail'),
    path('report_order_list/', views.report_order_list, name='report_order_list'),
    path('export/excel_order/', views.export_excel_order, name='export_excel_order'),

    path('suppliers/', views.suppliers, name='suppliers'),
    path('add-suppliers/', views.add_suppliers, name='add_suppliers'),
    path('suppliers/delete/<int:id>/', views.delete_suppliers, name='delete_suppliers'),
    path('detail-suppliers/<int:id>/', views.detail_suppliers, name='detail_suppliers'),
    path('suppliers-edit/<int:id>/', views.edit_suppliers, name='edit_suppliers'),

    path('category/', views.category, name='category'),
    path('add-category/', views.add_category, name='add_category'),
    path('category-edit/<int:id>/', views.edit_category, name='edit_category'),
    path('category/delete/<int:id>/', views.delete_category, name='delete_category'),

    path('workgroup/', views.workgroup, name='workgroup'),
    path('add_work_group/', views.add_work_group, name='add_work_group'),
    path('import_work_group/', views.import_work_group, name='import_work_group'),
    path('edit_workgroup/<int:id>/', views.edit_workgroup, name='edit_workgroup'),
    path('delete_workgroup/delete/<int:id>/', views.delete_workgroup, name='delete_workgroup'),


    path('subcategory/', views.subcategory, name='subcategory'),
    path('add-subcategory/', views.add_subcategory, name='add_subcategory'),
    path('subcategory-edit/<int:id>/', views.edit_subcategory, name='edit_subcategory'),
    path('subcategory/delete/<int:id>/', views.delete_subcategory, name='delete_subcategory'),


    path('stock/', views.stock, name='stock'),
    path('total_quantity/', views.total_quantity, name='total_quantity'),

    path('receive_product/', views.receive_product, name='receive_product'),
    path('receive_list/', views.receive_list, name='receive_list'),
    path('update_received_product/<int:id>/', views.update_received_product, name='update_received_product'),
    path('receive/delete/<int:id>/', views.delete_receive, name='delete_receive'),
    path('monthly_report/', views.monthly_report, name='monthly_report'),
    path('monthly_report/<int:year>/<int:month>/', views.monthly_report, name='monthly_report_with_date'),
    path('export-excel/', views.export_to_excel, name='export_to_excel'),
    path('upload/', views.upload_products, name='upload_products'),
    path('export-products/', views.export_products_to_excel, name='export_products'),
    path('record_monthly_stock/', views.record_monthly_stock_view, name='record_monthly_stock'),
    path('monthly-stock-records/', views.monthly_stock_records, name='monthly_stock_records'),
    path('monthly_stock_records/export/', views.export_monthly_stock_records_to_excel, name='export_monthly_stock_records'),
    path('monthly-stock-sum/', views.monthly_stock_sum, name='monthly_stock_sum'),
    path('export_monthly_stock_sum_to_excel/', views.export_monthly_stock_sum_to_excel, name='export_monthly_stock_sum_to_excel'),
    path('monthly-report-receive/', views.monthly_report_receive, name='monthly_report_receive'),
    path('export-to-excel-receive/', views.export_to_excel_receive, name='export_to_excel_receive'),
    path('report-monthly-totals/', views.report_monthly_totals, name='report_monthly_totals'),

    path('notification/', views.notification, name='notification'),
    path('notifications/<int:notification_id>/', views.acknowledge_notification, name='acknowledge_notification'),
    path('notifications/<int:notification_id>/restock/', views.restock_notification, name='restock_notification'),
    





]


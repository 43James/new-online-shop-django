from django.urls import path

from assets import views
# from .views import filter_by_category

app_name = "assets"

urlpatterns = [
	path('base_sidebar/', views.base, name='base_sidebar'),]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('companies/', views.companies_list, name='companies'),
    path('companies/<int:company_id>/', views.company_detail, name='company_detail'),
    path('bikes/<int:bike_id>/book/', views.book_bike, name='book_bike'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/add-company/', views.add_company, name='add_company'),
    path('admin-dashboard/manage-bikes/', views.manage_bikes, name='manage_bikes'),
    path('admin-dashboard/manage-bikes/edit/<int:bike_id>/', views.edit_bike, name='edit_bike'),
    path('admin-dashboard/manage-bikes/delete/<int:bike_id>/', views.delete_bike, name='delete_bike'),
    path('admin-dashboard/bookings/', views.admin_bookings, name='admin_bookings'),
]

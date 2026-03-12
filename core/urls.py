from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('companies/', views.companies_list, name='companies'),
    path('companies/<int:company_id>/', views.company_detail, name='company_detail'),
    path('bikes/<int:bike_id>/book/', views.book_bike, name='book_bike'),
    
    # Auth
    path('register/', views.register_user, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Payment
    path('payment/<int:booking_id>/', views.payment_checkout, name='payment_checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('my-bookings/', views.user_bookings, name='user_dashboard'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('refund-success/<int:booking_id>/', views.refund_success, name='refund_success'),
    # Vendor Dashboard
    path('vendor-dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor-dashboard/add-bike/', views.vendor_add_bike, name='vendor_add_bike'),
    path('vendor-dashboard/manage-bikes/', views.vendor_manage_bikes, name='vendor_manage_bikes'),
    path('vendor-dashboard/edit-bike/<int:bike_id>/', views.vendor_edit_bike, name='vendor_edit_bike'),
    path('vendor-dashboard/update-upi/', views.vendor_update_upi, name='vendor_update_upi'),
    path('vendor-dashboard/verifications/', views.vendor_verifications_list, name='vendor_verifications_list'),
    path('vendor-dashboard/verifications/<int:verification_id>/<str:action>/', views.vendor_approve_verification, name='vendor_approve_verification'),
    
    # User Profile / Identity
    path('verify-identity/', views.verify_identity, name='verify_identity'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/add-vendor/', views.add_vendor, name='add_vendor'),
    path('admin-dashboard/vendors/', views.manage_vendors, name='manage_vendors'),
    path('admin-dashboard/users/', views.manage_users, name='manage_users'),
    path('admin-dashboard/manage-bikes/', views.manage_bikes, name='manage_bikes'),
    path('admin-dashboard/manage-bikes/edit/<int:bike_id>/', views.edit_bike, name='edit_bike'),
    path('admin-dashboard/manage-bikes/delete/<int:bike_id>/', views.delete_bike, name='delete_bike'),
    path('admin-dashboard/bookings/', views.admin_bookings, name='admin_bookings'),
    path('admin-dashboard/bookings/edit/<int:booking_id>/', views.admin_edit_booking, name='admin_edit_booking'),
    path('admin-dashboard/users/toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('admin-dashboard/users/delete/<int:user_id>/', views.delete_user_admin, name='delete_user_admin'),
]

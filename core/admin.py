from django.contrib import admin
from .models import Company, Bike, Booking

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact', 'created_at')
    search_fields = ('name', 'location')

@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = ('bike_name', 'company', 'bike_type', 'price_per_hour', 'price_per_day', 'is_available')
    list_filter = ('is_available', 'bike_type', 'company')
    search_fields = ('bike_name', 'company__name')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('bike', 'user_name', 'company', 'booking_date', 'status', 'total_price')
    list_filter = ('status', 'booking_date', 'company')
    search_fields = ('user_name', 'user_contact', 'bike__bike_name')
    readonly_fields = ('total_price',)

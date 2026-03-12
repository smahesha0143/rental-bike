from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class UserProfile(models.Model):
    class RoleChoices(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        VENDOR = 'VENDOR', 'Vendor'
        USER = 'USER', 'User'
        
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.USER)
    identity_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_company', null=True, blank=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    contact = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    upi_qr_image = models.ImageField(upload_to='upi_qr/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Bike(models.Model):
    class BikeType(models.TextChoices):
        SCOOTER = 'Scooter', 'Scooter'
        SPORTS = 'Sports', 'Sports'
        ELECTRIC = 'Electric', 'Electric'
        CRUISER = 'Cruiser', 'Cruiser'
        DIRT = 'Dirt Bike', 'Dirt Bike'
        STANDARD = 'Standard', 'Standard'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bikes')
    bike_name = models.CharField(max_length=255)
    bike_type = models.CharField(max_length=50, choices=BikeType.choices)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='bikes/', blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bike_name} ({self.company.name})"

class Booking(models.Model):
    class DurationType(models.TextChoices):
        HOURS = 'Hours', 'Hours'
        DAYS = 'Days', 'Days'
        
    class BookingStatus(models.TextChoices):
        PAYMENT_PENDING = 'Payment Pending', 'Payment Pending'
        CONFIRMED = 'Confirmed', 'Confirmed'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'

    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, related_name='bookings')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    user_name = models.CharField(max_length=255)
    user_contact = models.CharField(max_length=50)
    booking_date = models.DateField()
    start_time = models.TimeField()
    duration_type = models.CharField(max_length=10, choices=DurationType.choices)
    duration_value = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PAYMENT_PENDING)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking for {self.bike.bike_name} by {self.user_name}"

    def calculate_price(self):
        if self.duration_type == self.DurationType.HOURS:
            return self.bike.price_per_hour * self.duration_value
        else:
            return self.bike.price_per_day * self.duration_value

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.calculate_price()
        super().save(*args, **kwargs)

class IdentityVerification(models.Model):
    class DocumentType(models.TextChoices):
        AADHAAR = 'Aadhaar', 'Aadhaar Card'
        PAN = 'PAN', 'PAN Card'
        DRIVING_LICENSE = 'Driving License', 'Driving License'
        PASSPORT = 'Passport', 'Passport'
        VISA = 'Visa', 'Visa'

    class VerificationStatus(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='identity_verification')
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    document_image = models.ImageField(upload_to='verification/documents/')
    selfie_image = models.ImageField(upload_to='verification/selfies/')
    status = models.CharField(max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_identities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Identity for {self.user.username} - {self.status}"

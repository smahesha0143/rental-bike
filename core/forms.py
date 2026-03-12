from django import forms
from .models import Company, Bike

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import Company, Bike, UserProfile

class VendorRegistrationForm(UserCreationForm):
    company_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}))
    company_location = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}))
    company_contact = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}))
    company_description = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'rows': 3}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Create UserProfile for Vendor
            UserProfile.objects.create(user=user, role=UserProfile.RoleChoices.VENDOR)
            # Create Company linked to this user
            Company.objects.create(
                user=user,
                name=self.cleaned_data['company_name'],
                location=self.cleaned_data['company_location'],
                contact=self.cleaned_data['company_contact'],
                description=self.cleaned_data['company_description']
            )
        return user

class BikeForm(forms.ModelForm):
    class Meta:
        model = Bike
        fields = ['company', 'bike_name', 'bike_type', 'price_per_hour', 'price_per_day', 'is_available', 'image', 'latitude', 'longitude']
        widgets = {
            'company': forms.Select(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border bg-white'}),
            'bike_name': forms.TextInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
            'bike_type': forms.Select(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border bg-white'}),
            'price_per_hour': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': '0.01'}),
            'price_per_day': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': '0.01'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'focus:ring-brand-500 h-4 w-4 text-brand-600 border-gray-300 rounded'}),
            'image': forms.ClearableFileInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
            'latitude': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': 'any'}),
        }

class VendorBikeForm(forms.ModelForm):
    class Meta:
        model = Bike
        fields = ['bike_name', 'bike_type', 'price_per_hour', 'price_per_day', 'is_available', 'image', 'latitude', 'longitude']
        widgets = {
            'bike_name': forms.TextInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
            'bike_type': forms.Select(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border bg-white'}),
            'price_per_hour': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': '0.01'}),
            'price_per_day': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': '0.01'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'focus:ring-brand-500 h-4 w-4 text-brand-600 border-gray-300 rounded'}),
            'image': forms.ClearableFileInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
            'latitude': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': 'any'}),
        }

class UpiUpdateForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['upi_qr_image']
        widgets = {
            'upi_qr_image': forms.ClearableFileInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
        }

from .models import IdentityVerification

class IdentityVerificationForm(forms.ModelForm):
    class Meta:
        model = IdentityVerification
        fields = ['document_type', 'document_image', 'selfie_image']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border bg-white'}),
            'document_image': forms.ClearableFileInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
            'selfie_image': forms.ClearableFileInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'capture': 'user'}),
        }

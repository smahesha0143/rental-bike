from django import forms
from .models import Company, Bike

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'location', 'contact', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
            'location': forms.TextInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
            'contact': forms.TextInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
            'description': forms.Textarea(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'rows': 3}),
        }

class BikeForm(forms.ModelForm):
    class Meta:
        model = Bike
        fields = ['company', 'bike_name', 'bike_type', 'price_per_hour', 'price_per_day', 'is_available', 'image']
        widgets = {
            'company': forms.Select(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border bg-white'}),
            'bike_name': forms.TextInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
            'bike_type': forms.Select(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border bg-white'}),
            'price_per_hour': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': '0.01'}),
            'price_per_day': forms.NumberInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border', 'step': '0.01'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'focus:ring-brand-500 h-4 w-4 text-brand-600 border-gray-300 rounded'}),
            'image': forms.ClearableFileInput(attrs={'class': 'shadow-sm focus:ring-brand-500 focus:border-brand-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border'}),
        }

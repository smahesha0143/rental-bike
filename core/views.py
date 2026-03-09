from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Company, Bike, Booking
from django.urls import reverse

def home(request):
    companies_count = Company.objects.count()
    bikes_count = Bike.objects.count()
    return render(request, 'core/home.html', {
        'companies_count': companies_count,
        'bikes_count': bikes_count
    })

def companies_list(request):
    companies = Company.objects.all().order_by('-created_at')
    return render(request, 'core/companies_list.html', {'companies': companies})

def company_detail(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    bikes = company.bikes.all() # using related_name
    return render(request, 'core/company_detail.html', {'company': company, 'bikes': bikes})

def book_bike(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    if not bike.is_available:
        messages.error(request, "This bike is currently not available.")
        return redirect('company_detail', company_id=bike.company.id)

    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        user_contact = request.POST.get('user_contact')
        booking_date = request.POST.get('booking_date')
        start_time = request.POST.get('start_time')
        duration_type = request.POST.get('duration_type')
        duration_value = int(request.POST.get('duration_value', 1))

        # create booking
        booking = Booking(
            bike=bike,
            company=bike.company,
            user_name=user_name,
            user_contact=user_contact,
            booking_date=booking_date,
            start_time=start_time,
            duration_type=duration_type,
            duration_value=duration_value
        )
        booking.save()
        
        # update bike status
        bike.is_available = False
        bike.save()

        messages.success(request, f"Successfully booked {bike.bike_name}! Total price: ₹{booking.total_price}")
        return redirect('companies')

    return render(request, 'core/book_bike.html', {'bike': bike})

# Admin Dashboard Views
from django.db.models import Sum
from .forms import CompanyForm, BikeForm

def admin_dashboard(request):
    total_bikes = Bike.objects.count()
    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    return render(request, 'core/admin_dashboard.html', {
        'total_bikes': total_bikes,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue
    })

def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company added successfully!')
            return redirect('admin_dashboard')
    else:
        form = CompanyForm()
    return render(request, 'core/add_company.html', {'form': form})

def manage_bikes(request):
    bikes = Bike.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = BikeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bike added successfully!')
            return redirect('manage_bikes')
    else:
        form = BikeForm()
        
    return render(request, 'core/manage_bikes.html', {'bikes': bikes, 'form': form})

def edit_bike(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    if request.method == 'POST':
        form = BikeForm(request.POST, request.FILES, instance=bike)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bike updated successfully!')
            return redirect('manage_bikes')
    else:
        form = BikeForm(instance=bike)
    return render(request, 'core/edit_bike.html', {'form': form, 'bike': bike})

def delete_bike(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    if request.method == 'POST':
        bike.delete()
        messages.success(request, 'Bike deleted successfully!')
        return redirect('manage_bikes')
    return render(request, 'core/delete_bike_confirm.html', {'bike': bike})

def admin_bookings(request):
    bookings = Booking.objects.all().order_by('-created_at')
    return render(request, 'core/admin_bookings.html', {'bookings': bookings})

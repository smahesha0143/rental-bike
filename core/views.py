from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Company, Bike, Booking
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

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

@login_required(login_url='login')
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

        # Create booking, but mark as payment pending
        booking = Booking(
            bike=bike,
            company=bike.company,
            user=request.user,  # Associate with logged-in user
            user_name=user_name,
            user_contact=user_contact,
            booking_date=booking_date,
            start_time=start_time,
            duration_type=duration_type,
            duration_value=duration_value,
            status=Booking.BookingStatus.PAYMENT_PENDING
        )
        booking.save()
        
        # We DO NOT lock the bike or mark it as unavailable here, waiting for payment confirmation

        return redirect('payment_checkout', booking_id=booking.id)

    return render(request, 'core/book_bike.html', {'bike': bike})

# --- Authentication Views ---

def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful. Welcome!')
            return redirect('home')
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
            # Re-render login page with signup tab open and errors shown
            login_form = AuthenticationForm()
            return render(request, 'core/login.html', {
                'form': login_form,
                'register_form': form,
                'show_signup': True,
            })
    return redirect('login')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    form = AuthenticationForm()
    register_form = UserCreationForm()
    return render(request, 'core/login.html', {
        'form': form,
        'register_form': register_form,
    })

def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

# --- Payment Views ---

@login_required(login_url='login')
def payment_checkout(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # ensure the user can't pay for already confirmed bookings
    if booking.status != Booking.BookingStatus.PAYMENT_PENDING:
        messages.error(request, 'This booking has already been processed or cancelled.')
        return redirect('companies')

    if request.method == 'POST':
        # Simulate payment processing success
        booking.status = Booking.BookingStatus.CONFIRMED
        booking.save()

        # Lock bike now that it's paid
        bike = booking.bike
        bike.is_available = False
        bike.save()

        messages.success(request, f"Payment successful! You have booked {booking.bike.bike_name}.")
        return redirect('payment_success')

    return render(request, 'core/payment_checkout.html', {'booking': booking})

@login_required(login_url='login')
def payment_success(request):
    return render(request, 'core/payment_success.html')

@login_required(login_url='login')
def user_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date', '-start_time')
    return render(request, 'core/user_dashboard.html', {'bookings': bookings})


@login_required(login_url='login')
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Only allow cancelling if Confirmed or Payment Pending
    if booking.status not in [Booking.BookingStatus.CONFIRMED, Booking.BookingStatus.PAYMENT_PENDING]:
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('user_dashboard')

    if request.method == 'POST':
        # Calculate refund: full refund for Confirmed, no refund for Payment Pending
        if booking.status == Booking.BookingStatus.CONFIRMED:
            booking.refund_amount = booking.total_price
        else:
            booking.refund_amount = 0

        booking.status = Booking.BookingStatus.CANCELLED
        booking.save()

        # Release the bike back to available
        bike = booking.bike
        bike.is_available = True
        bike.save()

        messages.success(request, 'Your booking has been cancelled successfully.')
        return redirect('refund_success', booking_id=booking.id)

    return render(request, 'core/cancel_booking_confirm.html', {'booking': booking})


@login_required(login_url='login')
def refund_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'core/refund_success.html', {'booking': booking})



# Admin Dashboard Views
from django.db.models import Sum
from .forms import CompanyForm, BikeForm

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    total_bikes = Bike.objects.count()
    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    return render(request, 'core/admin_dashboard.html', {
        'total_bikes': total_bikes,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue
    })

@user_passes_test(lambda u: u.is_staff)
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

@user_passes_test(lambda u: u.is_staff)
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

@user_passes_test(lambda u: u.is_staff)
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

@user_passes_test(lambda u: u.is_staff)
def delete_bike(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    if request.method == 'POST':
        bike.delete()
        messages.success(request, 'Bike deleted successfully!')
        return redirect('manage_bikes')
    return render(request, 'core/delete_bike_confirm.html', {'bike': bike})

@user_passes_test(lambda u: u.is_staff)
def admin_bookings(request):
    bookings = Booking.objects.all().order_by('booking_date', 'start_time')
    return render(request, 'core/admin_bookings.html', {'bookings': bookings})


@user_passes_test(lambda u: u.is_staff)
def admin_edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Booking.BookingStatus.choices):
            old_status = booking.status
            booking.status = new_status

            # If admin cancels, process refund and release bike
            if new_status == Booking.BookingStatus.CANCELLED and old_status == Booking.BookingStatus.CONFIRMED:
                booking.refund_amount = booking.total_price
                booking.bike.is_available = True
                booking.bike.save()

            # If admin confirms, lock the bike
            if new_status == Booking.BookingStatus.CONFIRMED and old_status != Booking.BookingStatus.CONFIRMED:
                booking.bike.is_available = False
                booking.bike.save()

            # If completed, release the bike
            if new_status == Booking.BookingStatus.COMPLETED:
                booking.bike.is_available = True
                booking.bike.save()

            booking.save()
            messages.success(request, f'Booking #{booking.id} status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status.')
    return redirect('admin_bookings')

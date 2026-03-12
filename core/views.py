from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Company, Bike, Booking, UserProfile, IdentityVerification
from django.urls import reverse
from django.db import transaction
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
@transaction.atomic
def book_bike(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    
    # Enforce Identity Verification (Bypass for staff/superusers)
    if not (request.user.is_staff or request.user.is_superuser):
        if not hasattr(request.user, 'profile') or not request.user.profile.identity_verified:
            messages.warning(request, "You must complete your identity verification before you can book a bike.")
            return redirect('verify_identity')
        
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
            UserProfile.objects.create(user=user, role=UserProfile.RoleChoices.USER)
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
        login_as = request.POST.get('login_as', 'USER')
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # For superuser/admin overriding
            if login_as == 'ADMIN' and (user.is_superuser or user.is_staff):
                # Ensure they have a profile, just in case
                profile, created = UserProfile.objects.get_or_create(user=user, defaults={'role': UserProfile.RoleChoices.ADMIN})
                # If they were an old superuser without ADMIN role, we can just optionally update or let them pass
                login(request, user)
                messages.success(request, f'Welcome back, Admin {username}!')
                return redirect('admin_dashboard')
            elif login_as == 'ADMIN':
                messages.error(request, 'You do not have Administrator privileges.')
                return redirect('login')

            profile, created = UserProfile.objects.get_or_create(user=user)
            if profile.role != login_as:
                messages.error(request, f'This account is not a {login_as.capitalize()} account.')
                return redirect('login')

            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            
            if profile.role == 'VENDOR':
                return redirect('vendor_dashboard')
            else:
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

        messages.success(request, 'Payment successful! Your bike is booked.')
        return redirect('payment_success')

    company = booking.company

    return render(request, 'core/payment_checkout.html', {
        'booking': booking,
        'company': company
    })

@login_required(login_url='login')
def payment_success(request):
    return render(request, 'core/payment_success.html')

@login_required(login_url='login')
def user_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date', '-start_time')
    try:
        verification = request.user.identity_verification
    except:
        verification = None
    
    # Fetch all available bikes for the "Find Nearby" map
    available_bikes = Bike.objects.filter(is_available=True)
        
    return render(request, 'core/user_dashboard.html', {
        'bookings': bookings, 
        'verification': verification,
        'available_bikes': available_bikes
    })

@login_required(login_url='login')
def verify_identity(request):
    try:
        verification = request.user.identity_verification
        if not (request.user.is_staff or request.user.is_superuser):
            if verification.status in [IdentityVerification.VerificationStatus.APPROVED, IdentityVerification.VerificationStatus.PENDING]:
                messages.info(request, f"Your identity verification is currently {verification.status}.")
                return redirect('user_dashboard')
    except:
        verification = None

    if request.method == 'POST':
        from .forms import IdentityVerificationForm
        if verification:
            form = IdentityVerificationForm(request.POST, request.FILES, instance=verification)
        else:
            form = IdentityVerificationForm(request.POST, request.FILES)
            
        if form.is_valid():
            iv = form.save(commit=False)
            iv.user = request.user
            iv.status = IdentityVerification.VerificationStatus.PENDING
            iv.save()
            messages.success(request, 'Identity verification submitted successfully! Please wait for vendor approval.')
            return redirect('user_dashboard')
    else:
        from .forms import IdentityVerificationForm
        if verification:
            form = IdentityVerificationForm(instance=verification)
        else:
            form = IdentityVerificationForm()
            
    return render(request, 'core/verify_identity.html', {'form': form, 'verification': verification})


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



# Admin & Vendor Dashboard Views
from django.db.models import Sum
from .forms import VendorRegistrationForm, BikeForm, VendorBikeForm, UpiUpdateForm

# --- Vendor Views ---

@login_required(login_url='login')
def vendor_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'VENDOR':
            return redirect('home')
        
    try:
        company = request.user.vendor_company
    except Company.DoesNotExist:
        if request.user.is_staff or request.user.is_superuser:
            messages.error(request, "Admins must be linked to a Company to view this dashboard.")
            return redirect('admin_dashboard')
        return redirect('home')
    total_bikes = company.bikes.count()
    total_bookings = company.bookings.count()
    total_revenue = company.bookings.filter(status__in=[Booking.BookingStatus.CONFIRMED, Booking.BookingStatus.COMPLETED]).aggregate(Sum('total_price'))['total_price__sum'] or 0
    bikes = company.bikes.all()
    
    return render(request, 'core/vendor_dashboard.html', {
        'company': company,
        'total_bikes': total_bikes,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'bikes': bikes
    })

@login_required(login_url='login')
def vendor_manage_bikes(request):
    if not (request.user.is_staff or request.user.is_superuser):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'VENDOR':
            return redirect('home')
    
    try:
        company = request.user.vendor_company    
    except:
        return redirect('home')
    bikes = company.bikes.all().order_by('-created_at')
    return render(request, 'core/vendor_manage_bikes.html', {'bikes': bikes, 'company': company})

@login_required(login_url='login')
def vendor_add_bike(request):
    if not (request.user.is_staff or request.user.is_superuser):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'VENDOR':
            return redirect('home')
        
    try:
        company = request.user.vendor_company
    except:
        return redirect('home')
    if request.method == 'POST':
        form = VendorBikeForm(request.POST, request.FILES)
        if form.is_valid():
            bike = form.save(commit=False)
            bike.company = company
            bike.save()
            messages.success(request, 'Bike added successfully!')
            return redirect('vendor_manage_bikes')
    else:
        form = VendorBikeForm()
    return render(request, 'core/vendor_edit_bike.html', {'form': form, 'title': 'Add Bike'})

@login_required(login_url='login')
def vendor_edit_bike(request, bike_id):
    if not (request.user.is_staff or request.user.is_superuser):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'VENDOR':
            return redirect('home')
        
    try:
        company = request.user.vendor_company
        bike = get_object_or_404(Bike, id=bike_id, company=company)
    except:
        bike = get_object_or_404(Bike, id=bike_id) # Admin can edit any bike
        company = bike.company
    if request.method == 'POST':
        form = VendorBikeForm(request.POST, request.FILES, instance=bike)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bike updated successfully!')
            return redirect('vendor_manage_bikes')
    else:
        form = VendorBikeForm(instance=bike)
    return render(request, 'core/vendor_edit_bike.html', {'form': form, 'title': 'Edit Bike', 'bike': bike})

@login_required(login_url='login')
def vendor_update_upi(request):
    if not (request.user.is_staff or request.user.is_superuser):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'VENDOR':
            return redirect('home')
        
    try:
        company = request.user.vendor_company
    except:
        return redirect('home')
    if request.method == 'POST':
        form = UpiUpdateForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'UPI QR updated successfully!')
            return redirect('vendor_dashboard')
    else:
        form = UpiUpdateForm(instance=company)
    return render(request, 'core/vendor_update_upi.html', {'form': form, 'company': company})

@login_required(login_url='login')
def vendor_verifications_list(request):
    if not (request.user.is_staff or request.user.is_superuser):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'VENDOR':
            return redirect('home')
        
    pending_verifications = IdentityVerification.objects.filter(status=IdentityVerification.VerificationStatus.PENDING).order_by('created_at')
    reviewed_verifications = IdentityVerification.objects.filter(verified_by=request.user).order_by('-updated_at')
    
    return render(request, 'core/vendor_verifications.html', {
        'pending': pending_verifications,
        'reviewed': reviewed_verifications
    })

@login_required(login_url='login')
def vendor_approve_verification(request, verification_id, action):
    if not (request.user.is_staff or request.user.is_superuser):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'VENDOR':
            return redirect('home')
        
    verification = get_object_or_404(IdentityVerification, id=verification_id)
    
    if action == 'approve':
        verification.status = IdentityVerification.VerificationStatus.APPROVED
        verification.user.profile.identity_verified = True
        verification.user.profile.save()
        messages.success(request, f'Identity for {verification.user.username} approved.')
    elif action == 'reject':
        verification.status = IdentityVerification.VerificationStatus.REJECTED
        verification.user.profile.identity_verified = False
        verification.user.profile.save()
        messages.warning(request, f'Identity for {verification.user.username} rejected.')
        
    verification.verified_by = request.user
    verification.save()
    
    return redirect('vendor_verifications_list')

# --- Admin Views ---

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
def add_vendor(request):
    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor added successfully!')
            return redirect('admin_dashboard')
    else:
        form = VendorRegistrationForm()
    return render(request, 'core/add_vendor.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
def manage_vendors(request):
    vendors = UserProfile.objects.filter(role=UserProfile.RoleChoices.VENDOR)
    return render(request, 'core/manage_vendors.html', {'vendors': vendors})

@user_passes_test(lambda u: u.is_staff)
def manage_users(request):
    users_list = UserProfile.objects.filter(role=UserProfile.RoleChoices.USER)
    return render(request, 'core/manage_users.html', {'users_list': users_list})

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

@user_passes_test(lambda u: u.is_staff)
def toggle_user_status(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user.is_superuser:
        messages.error(request, "Cannot block a superuser.")
    else:
        target_user.is_active = not target_user.is_active
        target_user.save()
        status = "unblocked" if target_user.is_active else "blocked"
        messages.success(request, f"User {target_user.username} has been {status}.")
    
    # Redirect back to whoever called (users or vendors list)
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

@user_passes_test(lambda u: u.is_staff)
def delete_user_admin(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user.is_superuser:
        messages.error(request, "Cannot delete a superuser.")
    else:
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User {username} has been deleted.")
    
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

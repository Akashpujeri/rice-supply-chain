import random
from datetime import datetime, timedelta
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings

from .forms import PasswordResetRequestForm, AdminProfileForm,UserPasswordChangeForm
from .models import AdminProfile
from dealer.models import DealerProfile
from manager.models import ManagerProfile,Purchase_paddy
from customer.models import CustomerProfile, Purchase_Rice

# Check if user is an admin
def check_admin(user):
    return user.is_authenticated and user.role == 'admin'

# Admin Dashboard View
@login_required(login_url='login')
@user_passes_test(check_admin)
def admin_dashboard(request):
    return render(request, 'admin/dashboard.html', {'role': 'admin'})

# Admin Profile View
@login_required(login_url='login')
@user_passes_test(check_admin)
def admin_profile(request):
    admin, _ = AdminProfile.objects.get_or_create(user=request.user)
    return render(request, "admin/admin_profile.html", {'admin': admin})

# Admin Profile Update View
@login_required(login_url='login')
@user_passes_test(check_admin)
def update_admin_profile(request):
    profile = get_object_or_404(AdminProfile, user=request.user)
    if request.method == "POST":
        form = AdminProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            updated_profile = form.save(commit=False)
            updated_profile.user = request.user
            updated_profile.save()
            return redirect("admin_profile")
    else:
        form = AdminProfileForm(instance=profile)
    return render(request, "admin/update_admin_profile.html", {'form': form})

def see_all_delears(request):
    delears = DealerProfile.objects.all()
    return render(request,"admin/see_all_delears.html",{'delears':delears})

def individuals_delear_details(request, id):
    dealer = get_object_or_404(DealerProfile, pk=id)
    paddy_stocks = dealer.paddystock_set.all()  # fetch all related paddy stocks
    return render(request, "admin/individuals_delear_details.html", {
        'dealer': dealer,
        'paddy_stocks': paddy_stocks
    })


def see_all_manager(request):
    managers = ManagerProfile.objects.all()
    return render(request,"admin/see_all_manager.html",{'managers':managers})

def individual_manager_details(request, id):
    manager = get_object_or_404(ManagerProfile, pk=id)
    return render(request, "admin/individual_manager_details.html", {'manager': manager})

def see_all_customers(request):
    customers = CustomerProfile.objects.all()
    return render(request, 'admin/see_all_customer.html', {'customers': customers})

def individual_customer_details(request, id):
    customer = get_object_or_404(CustomerProfile, pk=id)
    return render(request, 'admin/individuals_customer_details.html', {'customer': customer})

def delete_customer(request,id):
    customer = get_object_or_404(CustomerProfile, pk=id)
    if request.method == "POST":
        customer.delete()
        return redirect("see_all_customers")

def delete_manager(request,id):
    manager = get_object_or_404(ManagerProfile, pk=id)
    if request.method == "POST":
        manager.delete()
        return redirect("see_all_manager")


def delete_delear(request,id):
    delear = get_object_or_404(DealerProfile, pk=id)
    if request.method == "POST":
        delear.delete()
        return redirect("see_all_delears")

# Temporary OTP Storage
otp_storage = {}

# Send OTP to Email
def send_otp(email):
    otp = random.randint(100000, 999999)
    otp_storage[email] = {
        'otp': otp,
        'timestamp': datetime.now()
    }

    subject = "Password Reset OTP - RSCMS"
    message = f"Hello,\n\nYour OTP for password reset is: {otp}\n\nDo not share this OTP with anyone."
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

# Password Reset Request View
def request_password_reset(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            User = get_user_model()
            try:
                user = User.objects.filter(email=email).first
                send_otp(email)
                messages.success(request, "OTP has been sent to your email.")
                return redirect('verify_otp', email=email)
            except User.DoesNotExist:
                messages.error(request, "No user found with this email.")
    else:
        form = PasswordResetRequestForm()
    return render(request, "password_reset_and_change/request_password_reset.html", {'form': form})

# OTP Verification View
def verify_otp(request, email):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        data = otp_storage.get(email)

        if data:
            otp_valid = str(data['otp']) == entered_otp
            otp_expired = datetime.now() > data['timestamp'] + timedelta(minutes=5)

            if otp_valid and not otp_expired:
                del otp_storage[email]
                messages.success(request, "OTP verified successfully. Set a new password.")
                return redirect('reset_password', email=email)
            elif otp_expired:
                del otp_storage[email]
                messages.error(request, "OTP has expired. Please request a new one.")
            else:
                messages.error(request, "Invalid OTP. Please try again.")
        else:
            messages.error(request, "No OTP found for this email.")
    return render(request, "password_reset_and_change/verify_otp.html", {'email': email})

# Password Reset View
def reset_password(request, email):
    if request.method == "POST":
        new_password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if new_password == confirm_password:
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                user.password = make_password(new_password)
                user.save()
                messages.success(request, "Password reset successfully. Please login.")
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
        else:
            messages.error(request, "Passwords do not match. Try again.")
    return render(request, "password_reset_and_change/reset_password.html", {'email': email})


@login_required(login_url='login_user')
@user_passes_test(check_admin)
def change_password(request):
    if request.method == 'POST':
        form = UserPasswordChangeForm(data=request.POST, user=request.user)  # ✅ Corrected form initialization
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # ✅ Keep user logged in
            messages.success(request, "Your password was successfully updated!")
            return redirect('password_change_complete')  # ✅ Redirect instead of re-rendering
    else:
        form = UserPasswordChangeForm(user=request.user)

    return render(request, 'password_reset_and_change/change_password.html', {'form': form})

def password_change_complete(request):
    return render(request, 'password_reset_and_change/password_change_complete.html')



@login_required(login_url='login_user')
@user_passes_test(check_admin)
def customer_rice_purchases_history_seen_by_admin(request, id):
    customer_profile = get_object_or_404(CustomerProfile, id=id)
    
    # Get the associated user object
    customer_user = customer_profile.user
    
    # Filter by user, not profile
    purchases = Purchase_Rice.objects.filter(customer=customer_user, status="Successful").order_by("-purchase_date")
    print(purchases)
    
    context = {
        "purchases": purchases,
        "customer_profile": customer_profile
    }
    
    return render(request, "admin/customer_purchases_history.html", context)


@login_required(login_url='login_user')
@user_passes_test(check_admin)
def dealer_purchases_history(request, id):
    dealer_profile = get_object_or_404(DealerProfile, id=id)

    # Use DealerProfile instead of dealer_profile.user
    purchases = Purchase_paddy.objects.filter(paddy__dealer=dealer_profile, status="Successful")

    context = {
        "purchases": purchases,
    }

    return render(request, "admin/dealer_purchases_history.html", context)
    


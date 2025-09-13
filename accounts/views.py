# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from dealer.forms import DealerProfileForm
from .forms import CustomUserCreationForm

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        dealer_form = DealerProfileForm(request.POST)
        
        if form.is_valid():
            user = form.save()  # Save user first
            
            if user.role == 'dealer' and dealer_form.is_valid():
                dealer_profile = dealer_form.save(commit=False)
                dealer_profile.user = user  
                dealer_profile.save()    
            return redirect('login')  
    else:
        form = CustomUserCreationForm()
        dealer_form=DealerProfileForm()

    return render(request, 'accounts/auth/register.html', {'form': form,"dealer_form":dealer_form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return role_based_redirect(user)
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

# Redirect Logic
def role_based_redirect(user):
    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'manager':
        return redirect('manager_dashboard')
    elif user.role == 'dealer':
        return redirect('dealer_dashboard')
    elif user.role == 'customer':
        return redirect('explore_rice_post')
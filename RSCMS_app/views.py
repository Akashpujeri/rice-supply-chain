from django.shortcuts import render
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

def home(request):
    return render(request, 'home.html')
def about(request):
    return render(request, 'about.html')
def services(request):
    return render(request, 'services.html')

def contact_support(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Send email (optional)
        send_mail(
            f"Support Request from {name}",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],  # Your support email
        )
        messages.success(request, "Your message has been sent successfully!")
        
    return render(request, 'contact_support.html')

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404,redirect,HttpResponse
from .models import CustomerProfile, Purchase_Rice, Payment_For_Rice
from manager.models import RicePost
from .forms import PaymentForRiceForm
from decimal import Decimal
from .forms import CustomerProfileForm, PurchaseRiceForm
from django.contrib import messages

import uuid
import random
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q


from django.template.loader import render_to_string
from django.http import HttpResponse

from django.template.loader import get_template
import tempfile

from xhtml2pdf import pisa



def check_customer(user):
    return user.is_authenticated and user.role == 'customer'
def check_admin(user):
    return user.is_authenticated and user.role == 'admin'

def check_customer_or_admin(user):
    return check_customer(user) or check_admin(user)

@login_required(login_url='login')
@user_passes_test(check_customer)
def customer_dashboard(request):
    return render(request, 'customer/dashboard.html',{'role':'customer'})

@login_required(login_url='login')
@user_passes_test(check_customer)
def customer_profile(request):
    customer, created =CustomerProfile.objects.get_or_create(user=request.user)
    return render(request,"customer/customer_profile.html",{'customer':customer})

@login_required(login_url='login')
@user_passes_test(check_customer)
def update_customer_profile(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    if request.method == "POST":
        form = CustomerProfileForm(request.POST, request.FILES,instance=customer)
        if form.is_valid():
            form.save()
            return redirect("customer_profile")
    else:
        form = CustomerProfileForm(instance=customer)
    return render(request,"customer/update_customer_profile.html",{'form':form})


def update_customer_profile_by_admin(request,id):
    customer = get_object_or_404(CustomerProfile, pk=id)
    if request.method == "POST":
        form = CustomerProfileForm(request.POST, request.FILES,instance=customer)
        if form.is_valid():
            form.save()
            return redirect("see_all_customers")
    else:
        form = CustomerProfileForm(instance=customer)
    return render(request,"customer/update_customer_profile.html",{'form':form})


        
@login_required(login_url='login')
@user_passes_test(check_customer)
def purchase_rice_from_manager(request, id):
    rice = get_object_or_404(RicePost, id=id, is_sold=False)

    if request.method == "POST":
        form = PurchaseRiceForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            if purchase.quantity_purchased > rice.quantity_kg:
                form.add_error('quantity_purchased', "Not enough rice available.")
            else:
                purchase.customer = request.user
                purchase.rice = rice
                purchase.total_price = (Decimal(purchase.quantity_purchased) * rice.price_per_kg) + purchase.delivery_cost
                purchase.save()

                rice.quantity_kg -= purchase.quantity_purchased
                if rice.quantity_kg <= 0:
                    rice.is_sold = True
                rice.save()

                return redirect("mock_customer_rice_payment", purchase_id=purchase.id)
    else:
        form = PurchaseRiceForm()

    return render(request, "customer/purchase_rice.html", {'form': form, 'rice': rice})

@login_required
@user_passes_test(check_customer_or_admin)
def rice_purchases_history(request):
    purchases_rice = Purchase_Rice.objects.filter(customer=request.user).order_by("-purchase_date")
    # print(purchases_rice.payment)
    context = {
        "purchases_rice": purchases_rice
    }
    return render(request, "customer/purchase_history.html", context)

@login_required
@user_passes_test(check_customer)
def mock_customer_rice_payment(request, purchase_id):
    purchase = get_object_or_404(Purchase_Rice, pk=purchase_id, customer=request.user)

    if request.method == "POST":
        form = PaymentForRiceForm(request.POST)
        if form.is_valid():
           amount = form.cleaned_data['amount']
           if float(amount) == float(purchase.total_price):
               request.session["payment_amount"] = float(amount)
               return redirect('insert_phone_number_customer',purchase_id=purchase_id )
           
           messages.error(request, "Amount does not match the total price.")
           return render(request, "customer/payment/mock_customer_rice_payment.html", {
                "form": form,
                "purchase": purchase
            })
    else:
        form = PaymentForRiceForm(initial={'amount': purchase.total_price})

    return render(request, "customer/payment/mock_customer_rice_payment.html", {
        "form": form,
        "purchase": purchase
    })

@login_required
@user_passes_test(check_customer)
def insert_phone_number_customer(request,purchase_id):
    rice = get_object_or_404(Purchase_Rice,pk=purchase_id,customer=request.user) 
    
    if request.method == "POST":
        phone_number = request.POST.get('phone')
        if phone_number == rice.customer.customerprofile.phone_number:
            return redirect('send_purchases_otp_customer',email=rice.customer.customerprofile.user.email,purchase_id=purchase_id)
        else:
            messages.error(request,"Wrong phone number, insert the correct number")
            return redirect("insert_phone_number_customer",purchase_id=purchase_id)

    return render(request,"customer/payment/insert_phone_number.html")

otp_storage = {}
@login_required
@user_passes_test(check_customer)
def send_purchases_otp_customer(request,email,purchase_id):
    otp = random.randint(100000,999999)
    otp_storage[email] = {
        'otp' : otp,
        'timestamp' : datetime.now()
    }
    subject = "Transaction OTP - RSCMS"
    message = f"Assalamu Alaikum\n\nYour OTP for transaction is: {otp}\n\nNever share your Code and PIN with anyone.\n\nRSCMS never ask for this.\n\nExpiry: within 300 seconds"
    send_mail(subject,message,settings.EMAIL_HOST_USER, [email])
    
    return redirect("insert_otp_customer",purchase_id=purchase_id,email=email)
    
@login_required
@user_passes_test(check_customer)
def verify_purchases_otp_customer(request, email, purchase_id, otp):
    data = otp_storage.get(email)
    if data:
        otp_valid = data['otp'] == otp
        otp_expired = datetime.now() > data['timestamp'] + timedelta(minutes=5)

        if otp_valid and not otp_expired:
            del otp_storage[email]
            messages.success(request, "OTP verified successfully.")
            return redirect("insert_password_customer", purchase_id=purchase_id,email=email)
        elif otp_expired:
            del otp_storage[email]
            messages.error(request, "OTP has expired. Please request a new one.")
            return redirect('insert_phone_number_customer', purchase_id=purchase_id)
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect('insert_otp_customer', purchase_id=purchase_id, email=email)
    else:
        messages.error(request, "No OTP found for this email.")
        return redirect('insert_phone_number_customer', purchase_id=purchase_id)



@login_required
@user_passes_test(check_customer)
def insert_otp_customer(request,purchase_id,email):
    if request.method == "POST":
        otp = request.POST.get("otp")
        return redirect("verify_purchases_otp_customer",email=email,purchase_id=purchase_id,otp=otp)
    return render(request,"customer/payment/insert_otp.html",{'purchase_id':purchase_id})
    
@login_required
@user_passes_test(check_customer)
def insert_password_customer(request, purchase_id, email):
    purchase = get_object_or_404(Purchase_Rice, pk=purchase_id, customer=request.user)
    rice = purchase.rice
    amount = request.session.get('payment_amount')  # Get from session

    if not amount:
        messages.error(request, "Payment session expired.")
        return redirect('mock_customer_rice_payment', purchase_id=purchase_id)

    if request.method == "POST":
        password = request.POST.get('password')
        if password == purchase.customer.customerprofile.Transaction_password:
            # ✅ Now process payment
            payment = Payment_For_Rice.objects.create(
                user=request.user,
                rice=rice,
                amount=amount,
                transaction_id=f'MOCK-{uuid.uuid4().hex[:8]}',
                is_paid=True,
                status="Success"
            )
            purchase.payment = True
            purchase.save()

            del request.session['payment_amount']  # ✅ Clean up session
            messages.success(request, "Payment successful.")
            return redirect('mock_customer_rice_payment_success')
        else:
            messages.error(request, "Incorrect password.")
            return redirect("insert_password_customer", purchase_id=purchase_id, email=email)

    return render(request, "customer/payment/insert_password.html", {
        'purchase_id': purchase_id,
        'email': email
    })


@login_required
@user_passes_test(check_customer)
def mock_customer_rice_payment_success(request):
    return render(request, "customer/payment/success.html")

@login_required
@user_passes_test(check_customer)
def mock_customer_rice_payment_fail(request):
    return render(request, "customer/payment/fail.html")

def explore_rice_post(request):
    return redirect("explore_all_rice_post")

# Oder track
@login_required
@user_passes_test(lambda u: u.role == 'customer')
def my_order_page(request):
    orders = Purchase_Rice.objects.filter(customer=request.user).order_by("-purchase_date")
    return render(request, 'customer/my_order_page.html', {'orders': orders})

@login_required
# @require_POST
@user_passes_test(lambda u: u.role == 'customer')
def confirm_delivery(request, id):
    order = get_object_or_404(Purchase_Rice, id=id, customer=request.user)
    if order.status == "Delivered":
        if order.payment:
            order.status = "Successful"
            order.save()
            return redirect('my_order_page')
        else:
            return redirect('mock_rice_payment', id=order.id)
        
@login_required
@user_passes_test(lambda u: u.role == 'customer')
def download_receipt_for_buying_rice_for_customer(request, id):
    rice = get_object_or_404(Purchase_Rice, id=id, customer=request.user)
    price_per_kg = float(rice.total_price - rice.delivery_cost) / float(rice.quantity_purchased)

    html_content = render_to_string(
        "customer/receipt.html",
        {"rice": rice, "price_per_kg": price_per_kg},
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="receipt.pdf"'

    pisa_status = pisa.CreatePDF(html_content, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response

    
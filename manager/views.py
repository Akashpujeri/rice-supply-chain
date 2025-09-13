from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render,redirect,get_object_or_404,HttpResponse
from .models import ManagerProfile, RicePost, Purchase_paddy,PurchaseRice,PaymentForPaddy,PaymentForRice, PaddyStockOfManager,RiceStock
from dealer.models import Marketplace, PaddyStock,Marketplace
from .forms import ManagerProfileForm, RicePostForm, Purchase_paddyForm, PurchaseRiceForm,PaymentForPaddyForm, PaymentForRiceForm,RiceStockForm,PaddyStockForm
from decimal import Decimal
from django.db.models import Count, Sum, Avg
from customer.models import Purchase_Rice
from django.contrib import messages

import uuid
import random
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q


from django.template.loader import render_to_string
from django.http import HttpResponse
#from weasyprint import HTML
from reportlab.pdfgen import canvas

from django.template.loader import get_template
import tempfile

def check_manager(user):
    return user.is_authenticated and user.role == 'manager'

def check_manager_and_customer_and_admin(user):
    return user.is_authenticated and user.role in ['manager', 'customer','admin']

def check_manager_and_admin(user):
    return user.is_authenticated and user.role in ['manager','admin']

@login_required(login_url="login")
@user_passes_test(check_manager)
def manager_dashboard(request):
    return render(request, 'manager/dashboard.html')

@login_required(login_url="login")
@user_passes_test(check_manager)
def create_rice_post(request,id):
    rice_stock = get_object_or_404(RiceStock,id=id,manager=request.user)
    if request.method == "POST":
        form = RicePostForm(request.POST, request.FILES)
        if form.is_valid():
            rice_post = form.save(commit=False)
            rice_post.manager = request.user  
            try:
                rice_qty = float(request.POST.get('quantity_kg'))
            except (ValueError, TypeError):
                messages.error(request, "Invalid quantity format.")
                return redirect('rice_stock_report')
            if rice_qty>0 and rice_qty<=rice_stock.stock_quantity:
                rice_stock.stock_quantity -= rice_qty
                rice_stock.total_price -= Decimal(rice_qty*float(rice_stock.average_price_per_kg))
                rice_stock.save()
            else:
                messages.error(request,"Invalid Quantity or insufficient stock")
                return redirect('rice_stock_report')
            
            rice_post.save()
            return redirect("show_my_rice_post")
    else:
        form = RicePostForm()
    return render(request, "manager/create_rice_post.html", {'form': form})

@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def update_rice_post(request,id):
    rice_post = get_object_or_404(RicePost,id=id)
    if request.method == "POST":
        form = RicePostForm(request.POST, request.FILES, instance=rice_post)
        if form.is_valid():
            form.save()
            return redirect("show_my_rice_post")
    else:
        form = RicePostForm(instance=rice_post)
    return render(request,"manager/update_rice_post.html",{"form":form})


@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def delete_rice_post(request,id):
    rice_post = get_object_or_404(RicePost,id=id)
    if request.method == "POST":
        rice_post.delete()
        return redirect("show_rice_post")

@login_required(login_url="login")
@user_passes_test(check_manager_and_customer_and_admin)
def explore_all_rice_post(request):
    if request.user.role in ['admin','manager','customer']:
        rice_posts = RicePost.objects.filter( is_sold=False).order_by("-created_at")
    else:
        #TODO have to add a html file for this response
        return HttpResponse("Only admin, manager and customer can see this post")
    context = {
        "check" : 1,
        'rice_posts':rice_posts
    }
    return render(request,"manager/show_rice_post.html",context)

@login_required(login_url="login")
@user_passes_test(check_manager)
def show_my_rice_post(request):
    if request.user.role in ['manager']:
        rice_posts = RicePost.objects.filter(manager=request.user, is_sold=False).order_by("-created_at")
    else:
        #TODO have to add a html file for this response
        return HttpResponse("Only manager can see this post")
    context = {
        "check" : 2,
        'rice_posts':rice_posts
    }
    return render(request,"manager/show_rice_post.html",context)

def individual_rice_post_detail(request,id):
    rice_post = get_object_or_404(RicePost,id=id)
    return render(request,"manager/individual_rice_post_detail.html",{'post':rice_post})

@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def update_manager_profile(request):
    profile = get_object_or_404(ManagerProfile, user=request.user)

    if request.method == "POST":
        form = ManagerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("manager_profile")  
    else:
        form = ManagerProfileForm(instance=profile)

    return render(request, "manager/update_manager_profile.html", {'form': form})


def update_manager_profile_by_admin(request,id):
    profile = get_object_or_404(ManagerProfile, pk=id)

    if request.method == "POST":
        form = ManagerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("see_all_manager")
    else:
        form = ManagerProfileForm(instance=profile)

    return render(request, "manager/update_manager_profile.html", {'form': form})


@login_required(login_url="login")
@user_passes_test(check_manager)
def manager_profile(request):
    manager, created = ManagerProfile.objects.get_or_create(user=request.user)
    return render(request,"manager/manager_profile.html",{'manager':manager})
    
@login_required(login_url="login")
@user_passes_test(check_manager)
def explore_paddy_post(request):
    
    sort = request.GET.get('sort', 'recent')

    posts = Marketplace.objects.filter(is_available=True)

    if sort == 'price_asc':
        posts = posts.order_by('price_per_kg')
    elif sort == 'price_desc':
        posts = posts.order_by('-price_per_kg')
    elif sort == 'moisture':
        posts = posts.order_by('moisture_content')
    else:  # ' By Default
        posts = posts.order_by('-stored_since')

    avg_price = posts.aggregate(avg=Avg('price_per_kg'))['avg']
    total_quantity = posts.aggregate(total=Sum('quantity'))['total'] or 0
    top_dealer = posts.values('dealer__user__username').annotate(post_count=Count('id')).order_by('-post_count').first()

    return render(request, 'dealer/paddy_posts.html', {
        'posts': posts,
        'avg_price': avg_price,
        'total_quantity': total_quantity,
        'top_dealer': top_dealer['dealer__user__username'] if top_dealer else None,
        'current_sort': sort,
    })
   

@login_required(login_url="login")
@user_passes_test(check_manager)
def purchase_paddy(request,id):
    paddy = get_object_or_404(Marketplace, id=id , is_available=True)
    if request.method == "POST":
        form = Purchase_paddyForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            
            if purchase.quantity_purchased > paddy.quantity:
                form.add_error('quantity_purchased', "Not enough stock available.")
                return render(request, "manager/purchase_paddy.html", {'form': form, 'paddy': paddy})
            
            purchase.manager = request.user
            purchase.paddy = paddy
            purchase.total_price = Decimal((purchase.quantity_purchased/40.0) * float(paddy.price_per_kg)) + purchase.transport_cost
            purchase.save()
            
            paddy.quantity=paddy.quantity -  (Decimal(purchase.quantity_purchased))
            if paddy.quantity <= 0:
                paddy.is_available = False
            paddy.save()
            return redirect("my_paddy_order")
    else:
        form = Purchase_paddyForm()
    return render(request, "manager/purchase_paddy.html",{'form':form , 'paddy':paddy})
    
@login_required(login_url="login")
@user_passes_test(check_manager)
def purchase_rice(request, id):
    rice = get_object_or_404(RicePost,id=id)
    if request.method == "POST":
        form = PurchaseRiceForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False) 
            
            if purchase.quantity_purchased > rice.quantity_kg:
                form.add_error('quantity_purchased', "Not enough rice available.")
                return render(request, "manager/purchase_rice.html", {'form': form, 'rice': rice})
            
            purchase.manager = request.user
            purchase.rice  = rice 
            purchase.total_price = (Decimal(purchase.quantity_purchased)*rice.price_per_kg) + purchase.delivery_cost
            purchase.save()
            rice.quantity_kg = rice.quantity_kg - purchase.quantity_purchased  
            if rice.quantity_kg <= 0:
                rice.is_sold = True  
            rice.save() 
            return redirect("my_rice_order")
    else:
        form = PurchaseRiceForm() 
    return render(request, "manager/purchase_rice.html",{'form':form , 'rice':rice})


@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def purchase_history(request):
    purchases_paddy = Purchase_paddy.objects.filter(manager=request.user,status="Successful").order_by("-purchase_date")
    selling_rice = Purchase_Rice.objects.filter(rice__manager=request.user,status="Successful").order_by("-purchase_date")
    
    purchases_rice_from_others_manager = PurchaseRice.objects.filter(manager=request.user,status="Successful").order_by("-purchase_date")
    selling_rice_to_managers = PurchaseRice.objects.filter(rice__manager=request.user,status="Successful").order_by("-purchase_date")

    context = {
        "purchases_paddy": purchases_paddy,
        "purchases_rice": purchases_rice_from_others_manager,
        "seling_rice": selling_rice,
        "seling_rice_to_managers": selling_rice_to_managers,
    }

    return render(request, "manager/purchase_history.html", context)


@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def purchase_history_seen_admin(request, id):
    manager_profile = get_object_or_404(ManagerProfile, id=id)

    purchases_paddy = Purchase_paddy.objects.filter(manager=manager_profile.user,status="Successful").order_by("-purchase_date")
    purchases_rice = PurchaseRice.objects.filter(manager=manager_profile.user,status="Successful").order_by("-purchase_date")
    seling_rice = Purchase_Rice.objects.filter(rice__manager=manager_profile.user,status="Successful").order_by("-purchase_date")
    seling_rice_to_managers = PurchaseRice.objects.filter(rice__manager=manager_profile.user,status="Successful").order_by("-purchase_date")
    # print(seling_rice_to_managers)
    context = {
        'check':1,
        "manager": manager_profile,
        "purchases_paddy": purchases_paddy,
        "purchases_rice": purchases_rice,
        "seling_rice": seling_rice,
        "seling_rice_to_managers": seling_rice_to_managers,
    }

    return render(request, "manager/purchase_history.html", context)

# Mock payment Getaway for paddy
@login_required
def mock_paddy_payment(request, purchase_id):
    purchase = get_object_or_404(Purchase_paddy, pk=purchase_id, manager=request.user)

    if request.method == 'POST':
        form = PaymentForPaddyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if amount == purchase.total_price:
                request.session['payment_amount'] = float(amount)
                return redirect('insert_phone_number', purchase_id=purchase_id)
            else:
                messages.error(request, "Amount does not match the total price.")
                return redirect('mock_paddy_payment', purchase_id=purchase_id)
    else:
        form = PaymentForPaddyForm()

    context = {
        'purchase': purchase,
        'form': form,
    }
    return render(request, 'manager/payment/mock_paddy_payment.html', context)

@login_required
def insert_phone_number(request,purchase_id):
    paddy = get_object_or_404(Purchase_paddy,pk=purchase_id,manager=request.user)
    # print(paddy.manager.managerprofile.phone_number)
    if request.method == 'POST':
        phone_number = request.POST.get('phone')
        if phone_number == paddy.manager.managerprofile.phone_number:
            return redirect("send_purchases_otp",email=paddy.manager.managerprofile.user.email,purchase_id=purchase_id)
        else:
            messages.error(request,"Wrong phone number, insert the correct number")
            return redirect("insert_phone_number",purchase_id=purchase_id)
    return render(request,"manager/payment/insert_phone_number.html")


otp_storage = {}
@login_required
def send_purchases_otp(request,email,purchase_id):
    otp = random.randint(100000,999999)
    otp_storage[email] = {
        'otp' : otp,
        'timestamp' : datetime.now()
    }
    subject = "Transaction OTP - RSCMS"
    message = f"Have a Good Day!\n\nYour OTP for transaction is: {otp}\n\nNever share your Code and PIN with anyone.\n\nRSCMS never ask for this.\n\nExpiry: within 300 seconds"
    send_mail(subject,message,settings.EMAIL_HOST_USER, [email])
    
    return redirect("insert_otp",purchase_id=purchase_id,email=email)
    
    
@login_required
def verify_purchases_otp(request, email, purchase_id, otp):
    data = otp_storage.get(email)
    if data:
        otp_valid = data['otp'] == otp
        otp_expired = datetime.now() > data['timestamp'] + timedelta(minutes=5)

        if otp_valid and not otp_expired:
            del otp_storage[email]
            messages.success(request, "OTP verified successfully.")
            return redirect("insert_password", purchase_id=purchase_id,email=email)
        elif otp_expired:
            del otp_storage[email]
            messages.error(request, "OTP has expired. Please request a new one.")
            return redirect('insert_phone_number', purchase_id=purchase_id)
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect('insert_otp', purchase_id=purchase_id, email=email)
    else:
        messages.error(request, "No OTP found for this email.")
        return redirect('insert_phone_number', purchase_id=purchase_id)


@login_required
def insert_otp(request,purchase_id,email):
    if request.method == "POST":
        otp = request.POST.get("otp")
        return redirect("verify_purchases_otp",email=email,purchase_id=purchase_id,otp=otp)
    return render(request,"manager/payment/insert_otp.html",{'purchase_id':purchase_id})
    
@login_required
def insert_password(request, purchase_id, email):
    purchase = get_object_or_404(Purchase_paddy, pk=purchase_id, manager=request.user)
    paddy = purchase.paddy
    amount = request.session.get('payment_amount')  

    if not amount:
        messages.error(request, "Payment session expired.")
        return redirect('mock_paddy_payment', purchase_id=purchase_id)

    if request.method == "POST":
        password = request.POST.get('password')
        if password == purchase.manager.managerprofile.transaction_password:
            
            payment = PaymentForPaddy.objects.create(
                user=request.user,
                paddy=paddy,
                amount=amount,
                transaction_id=f'MOCK-{uuid.uuid4().hex[:8]}',
                is_paid=True,
                status="Success"
            )
            purchase.payment = True
            purchase.save()

            del request.session['payment_amount'] 
            messages.success(request, "Payment successful.")
            return redirect('mock_paddy_payment_success')
        else:
            messages.error(request, "Incorrect password.")
            return redirect("insert_password", purchase_id=purchase_id, email=email)

    return render(request, "manager/payment/insert_password.html", {
        'purchase_id': purchase_id,
        'email': email
    })


@login_required
def mock_paddy_payment_success(request):
    return render(request,"manager/payment/mock_paddy_payment_success.html")

@login_required
def mock_paddy_payment_fail(request):
    return render(request,"manager/payment/mock_paddy_payment_fail.html")


# Mock payment Getaway for rice
@login_required
def mock_rice_payment(request,rice_id):
    purchase =get_object_or_404(PurchaseRice,pk=rice_id, manager=request.user)
    if request.method == "POST":
        form = PaymentForRiceForm(request.POST)
        
        if form.is_valid():
           amount = form.cleaned_data['amount']
           if amount == purchase.total_price:
               request.session['payment_amount'] = float(amount)
               return redirect('insert_phone_number_for_rice',purchase_id=rice_id)
        else:
            messages.error(request,"Amount does not match the total price")
            return redirect('mock_rice_payment',purchase_id=rice_id)
                
    else:
        form = PaymentForRiceForm()
    context = {
        "form" : form,
        'purchase' : purchase
    }
    return render(request,"manager/payment/mock_rice_payment.html",context)

@login_required
def insert_phone_number_for_rice(request,purchase_id):
    rice = get_object_or_404(PurchaseRice,pk=purchase_id,manager=request.user)
    # print(rice.manager.managerprofile.phone_number)
    if request.method == 'POST':
        phone_number = request.POST.get('phone')
        if phone_number == rice.manager.managerprofile.phone_number:
            return redirect("send_purchases_otp_for_rice",email=rice.manager.managerprofile.user.email,purchase_id=purchase_id)
        else:
            messages.error(request,"Wrong phone number, insert the correct number")
            return redirect("insert_phone_number_for_rice",purchase_id=purchase_id)
    return render(request,"manager/payment/insert_phone_number.html")

otp_storage_for_rice = {}
@login_required
def send_purchases_otp_for_rice(request,email,purchase_id):
    otp = random.randint(100000,999999)
    otp_storage_for_rice[email] = {
        'otp' : otp,
        'timestamp' : datetime.now()
    }
    subject = "Transaction OTP - RSCMS"
    message = f"Have a Good Day!\n\nYour OTP for transaction is: {otp}\n\nNever share your Code and PIN with anyone.\n\nRSCMS never ask for this.\n\nExpiry: within 300 seconds"
    send_mail(subject,message,settings.EMAIL_HOST_USER, [email])
    
    return redirect("insert_otp_for_rice",purchase_id=purchase_id,email=email)
    
@login_required
def verify_purchases_otp_for_rice(request, email, purchase_id, otp):
    data = otp_storage_for_rice.get(email)
    if data:
        otp_valid = data['otp'] == otp
        otp_expired = datetime.now() > data['timestamp'] + timedelta(minutes=5)

        if otp_valid and not otp_expired:
            del otp_storage_for_rice[email]
            messages.success(request, "OTP verified successfully.")
            return redirect("insert_password_for_rice", purchase_id=purchase_id,email=email)
        elif otp_expired:
            del otp_storage_for_rice[email]
            messages.error(request, "OTP has expired. Please request a new one.")
            return redirect('insert_phone_number_for_rice', purchase_id=purchase_id)
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect('insert_otp_for_rice', purchase_id=purchase_id, email=email)
    else:
        messages.error(request, "No OTP found for this email.")
        return redirect('insert_phone_number_for_rice', purchase_id=purchase_id)


@login_required
def insert_otp_for_rice(request,purchase_id,email):
    if request.method == "POST":
        otp = request.POST.get("otp")
        return redirect("verify_purchases_otp_for_rice",email=email,purchase_id=purchase_id,otp=otp)
    return render(request,"manager/payment/insert_otp.html",{'purchase_id':purchase_id})
    
@login_required
def insert_password_for_rice(request, purchase_id, email):
    purchase = get_object_or_404(PurchaseRice, pk=purchase_id, manager=request.user)
    rice = purchase.rice
    amount = request.session.get('payment_amount')  

    if not amount:
        messages.error(request, "Payment session expired.")
        return redirect('mock_rice_payment', purchase_id=purchase_id)

    if request.method == "POST":
        password = request.POST.get('password')
        if password == purchase.manager.managerprofile.transaction_password:
           
            payment = PaymentForRice.objects.create(
                user=request.user,
                rice=rice,
                amount=amount,
                transaction_id=f'MOCK-{uuid.uuid4().hex[:8]}',
                is_paid=True,
                status="Success"
            )
            purchase.payment = True
            purchase.save()

            del request.session['payment_amount']  
            messages.success(request, "Payment successful.")
            return redirect('mock_rice_payment_success')
        else:
            messages.error(request, "Incorrect password.")
            return redirect("insert_password_for_rice", purchase_id=purchase_id, email=email)

    return render(request, "manager/payment/insert_password.html", {
        'purchase_id': purchase_id,
        'email': email
    })

@login_required
def mock_rice_payment_success(request):
    return render(request,"manager/payment/mock_rice_payment_success.html")

@login_required
def mock_rice_payment_fail(request):
    return render(request,"manager/payment/mock_rice_payment_fail.html")


# Search functionality
@login_required
def search(request):
    query = request.GET.get('query')  
    rice_results = []
    paddy_results = []

    user = request.user
    print(query)
    if user.is_authenticated:
        if user.role in ["manager", "admin"]:
            if query:
                rice_results = RicePost.objects.filter(
                    Q(rice_name__icontains=query) |
                    Q(description__icontains=query)
                )
                paddy_results = Marketplace.objects.filter(
                    Q(name__icontains=query)
                )
                all = Marketplace.objects.all()
                print(all)

        elif user.role == "dealer":
            if query:
                paddy_results = Marketplace.objects.filter(
                    Q(name__icontains=query)
                )

        elif user.role == "customer":
            if query:
                rice_results = RicePost.objects.filter(
                    Q(rice_name__icontains=query)
                )

    context = {
        'query': query,
        'rice_results': rice_results,
        'paddy_results': paddy_results,
    }
    return render(request, 'manager/search_results.html', context)

# My rice order and track that i order to another manager
def my_rice_order(request):
    orders = PurchaseRice.objects.filter(manager=request.user).order_by("-purchase_date")
    return render(request,"manager/my_rice_order.html",{"orders":orders})

# after delivery rice order from another manager i have to update status as confirm
@login_required
def confirm_rice_delivery_done_by_other_manager(request, id):
    order = get_object_or_404(PurchaseRice, id=id, manager=request.user)

    if order.status == "Delivered":
        if order.payment:
            order.status = "Successful"
            order.save()
            messages.success(request, "Order successfully confirmed.")
            return redirect("my_rice_order")
        else:
            messages.warning(request, "Please complete payment before confirming delivery.")
            return redirect("mock_rice_payment", id=order.id)

    messages.info(request, "Order must be in 'Delivered' status to confirm.")
    return redirect("my_rice_order")


# Oder track for rice that comes from customer and others manager
@login_required
@user_passes_test(lambda u: u.role == 'manager')
def incoming_order(request):
    orders = Purchase_Rice.objects.filter(rice__manager=request.user).order_by("-purchase_date")
    rice_orders = PurchaseRice.objects.filter(rice__manager=request.user).order_by("-purchase_date")
    return render(request, 'manager/incoming_order.html', {'orders': orders,'rice_orders':rice_orders})

# rice order from customer that i have to accept
@login_required
@user_passes_test(lambda u: u.role == 'manager')
def accept_rice_order_from_customer(request, id):
    if request.method == "POST":
        order = get_object_or_404(Purchase_Rice, id=id, rice__manager=request.user)
        new_status = request.POST.get("new_status")
        if new_status in ["Accepted", "Cancel"] and order.status == "Pending":
            order.status = new_status
            order.save()
    return redirect('incoming_order')


# after accepting order update oder transaction status
@login_required
@user_passes_test(lambda u: u.role == 'manager')
def update_order_status_for_customer(request, id):
    order = get_object_or_404(Purchase_Rice, id=id, rice__manager=request.user)

    if request.method == "POST":
        new_status = request.POST.get("new_status")
        valid_transitions = {
            "Accepted": ["Shipping", "Cancel"],
            "Shipping": ["Delivered"],
            "Delivered": ["Successful"],  
        }

        if new_status in valid_transitions.get(order.status, []):
            order.status = new_status
            order.save()

    return redirect('incoming_order')

# Order and delivery track for paddy that i order to dealer
@login_required
@user_passes_test(lambda u: u.role == 'manager')
def my_paddy_order(request):
    orders = Purchase_paddy.objects.filter(manager=request.user).order_by("-purchase_date")
    return render(request, 'manager/my_paddy_order.html', {'orders': orders})

# after receiving order from dealer i have to update status of delivery as confirm
@login_required
@user_passes_test(lambda u: u.role == 'manager')
def confirm_paddy_delivery(request, id):
    order = get_object_or_404(Purchase_paddy, id=id, manager=request.user)
    if order.status == "Delivered":
        if order.payment:
            order.status = "Successful"
            order.save()
            return redirect('my_paddy_order')
        else:
            return redirect('mock_paddy_payment', id=order.id)
        
# rice order from manager that i have to accept
@login_required
@user_passes_test(lambda u: u.role == 'manager')
def accept_rice_order_from_manager(request, id):
    if request.method == "POST":
        order = get_object_or_404(PurchaseRice, id=id, rice__manager=request.user)
        new_status = request.POST.get("new_status")
        if new_status in ["Accepted", "Cancel"] and order.status == "Pending":
            order.status = new_status
            order.save()
    return redirect('incoming_order')


# after accepting order update oder transaction status
@login_required
@user_passes_test(lambda u: u.role == 'manager')
def update_order_status_for_manager(request, id):
    order = get_object_or_404(PurchaseRice, id=id, rice__manager=request.user)

    if request.method == "POST":
        new_status = request.POST.get("new_status")
        valid_transitions = {
            "Accepted": ["Shipping", "Cancel"],
            "Shipping": ["Delivered"],
            "Delivered": ["Successful"],  
        }

        if new_status in valid_transitions.get(order.status, []):
            order.status = new_status
            order.save()

    return redirect('incoming_order')


from django.db.models import Sum
# Paddy Quantity calculation
@login_required
@user_passes_test(lambda u: u.role == "manager")
def paddy_stock_report(request):
    """View all paddy stock for the logged-in manager."""
    paddy_stocks = PaddyStockOfManager.objects.filter(manager=request.user).order_by("-updated_at")
    return render(
        request,
        "manager/stock/paddy_stock_report.html",
        {"paddy_stocks": paddy_stocks},
    )


@login_required
@user_passes_test(lambda u: u.role == "manager")
def manager_stock_management(request):
    """Main stock management dashboard for manager."""
    return render(request, "manager/stock/stock_management.html")


def estimate_rice_from_paddy(paddy_kg, yield_percentage=65):
    """Estimate rice quantity from given paddy quantity based on yield %."""
    return round((paddy_kg * yield_percentage) / 100, 2)


@login_required
@user_passes_test(lambda u: u.role == "manager")
def process_paddy_to_rice(request, stock_id):
    """Convert paddy stock into rice stock for the manager."""
    stock = get_object_or_404(PaddyStockOfManager, id=stock_id, manager=request.user)

    if request.method == "POST":
        try:
            process_qty = float(request.POST.get("process_quantity"))
            process_rice_name = request.POST.get("rice_name")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")
            return redirect("paddy_stock_report")

        if process_qty <= 0 or process_qty > stock.total_quantity:
            messages.error(request, "Invalid or insufficient quantity.")
            return redirect("paddy_stock_report")

        # Calculate rice from paddy (default 65% yield)
        processed_rice = estimate_rice_from_paddy(process_qty)

        # Update paddy stock
        stock.total_quantity -= process_qty
        if stock.total_quantity <= 0:
            stock.total_quantity = 0
            stock.is_active = False
        stock.total_price -= Decimal(process_qty * float(stock.average_price_per_kg))
        stock.save()

        # Update or create rice stock
        rice_stock, created = RiceStock.objects.get_or_create(
            manager=request.user,
            rice_name=process_rice_name,
            defaults={"stock_quantity": 0, "average_price_per_kg": 0},
        )

        total_rice_qty = rice_stock.stock_quantity + processed_rice
        rice_stock.total_price = (
            rice_stock.stock_quantity * float(rice_stock.average_price_per_kg)
        ) + (process_qty * float(stock.average_price_per_kg))

        rice_stock.stock_quantity = total_rice_qty
        rice_stock.average_price_per_kg = round(
            Decimal(rice_stock.total_price) / Decimal(total_rice_qty), 2
        )
        rice_stock.save()

        messages.success(
            request,
            f"Successfully processed {process_qty} kg of paddy into {processed_rice} kg of rice.",
        )

    return redirect("rice_stock_report")


@login_required
@user_passes_test(lambda u: u.role == "manager")
def rice_stock_report(request):
    """View all rice stock for the logged-in manager."""
    rice_stocks = RiceStock.objects.filter(manager=request.user).order_by("-updated_at")
    return render(
        request,
        "manager/stock/rice_stock_report.html",
        {"rice_stocks": rice_stocks},
    )


from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import RiceStock   # adjust model import if needed

def download_rice_stock_report(request):
    # Get rice stock data
    stocks = RiceStock.objects.all()

    # Load the template
    template_path = "manager/stock/rice_stock_pdf.html"  # use a separate clean template for PDF
    context = {"stocks": stocks}

    # Render template as string
    template = get_template(template_path)
    html = template.render(context)

    # Create PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="rice_stock_report.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    # If error
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    
    return response

@login_required
@user_passes_test(check_manager)
def download_paddy_stock_report(request):
    manager = request.user
    paddy_stocks = PaddyStockOfManager.objects.filter(manager=manager)

    # Calculate total stock
    total_paddy_stock = sum(stock.total_quantity for stock in paddy_stocks)

    # Render HTML template
    html_content = render_to_string(
        "manager/pdf_download/paddy_stock_report_pdf.html",
        {
            "manager": manager,
            "paddy_stocks": paddy_stocks,
            "total_paddy_stock": total_paddy_stock,
        },
    )

    # Setup PDF response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="paddy_stock_report.pdf"'

    # Generate PDF with pisa
    pisa_status = pisa.CreatePDF(html_content, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    return response

@login_required
@user_passes_test(check_manager)    
def edit_rice_stock(request,id):
    stock = get_object_or_404(RiceStock,id=id, manager=request.user)
    if request.method == "POST":
        form = RiceStockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request,"Rice stock updated successfully!")
            return redirect('rice_stock_report')
        else:
            messages.error(request,"There is something error, please try again")
            return redirect('edit_rice_stock',id)
    else:
        form = RiceStockForm(instance=stock)
    return render(request,"manager/stock/edit_rice_stock.html",{'form':form})

@login_required
@user_passes_test(check_manager)
def rice_stock_update(request):
    if request.method == "POST":
        form = RiceStockForm(request.POST,request.FILES)
        if form.is_valid():
            update_rice_stock = form.save(commit=False)
            update_rice_stock.manager = request.user
            update_rice_stock.save()
            messages.success(request,"Rice stock updated successfully")
            return redirect(rice_stock_report)
        else:
            messages.error(request,"Rice stock update failed")
            return redirect("rice_stock_update")
            
    else:
        form = RiceStockForm()
    return render(request,"manager/stock/edit_rice_stock.html",{'form':form})

@login_required(login_url="login")
@user_passes_test(check_manager)
def delete_rice_stock(request, id):
    rice_stock = get_object_or_404(RiceStock, id=id, manager=request.user)
    
    if request.method == "POST":
        rice_stock.delete()
        messages.success(request, "Rice stock deleted successfully!")
        return redirect("rice_stock_report")
    
    # Optional: If someone tries to access via GET, redirect back
    return redirect("rice_stock_report")

@login_required
@user_passes_test(check_manager)
def edit_paddy_stock(request, id):
    stock = get_object_or_404(PaddyStockOfManager, id=id, manager=request.user)
    
    if request.method == 'POST':
        form = PaddyStockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, "Paddy stock updated successfully!")
            return redirect('paddy_stock_report')
        else:
            messages.error(request, "There was an error in the form. Please correct it.")
    else:
        form = PaddyStockForm(instance=stock)

    return render(request, "manager/stock/edit_paddy_stock.html", {'form': form})


@login_required
@user_passes_test(check_manager)
def paddy_stock_update(request):
    if request.method == "POST":
        form = PaddyStockForm(request.POST,request.FILES)
        if form.is_valid():
            update_paddy_stock = form.save(commit=False)
            update_paddy_stock.manager = request.user
            update_paddy_stock.save()
            messages.success(request,"Paddy stock updated successfully")
            return redirect(paddy_stock_report)
        else:
            messages.error(request,"Paddy stock update failed, Please Try again")
            return redirect("paddy_stock_update") 
    else:
        form = PaddyStockForm()
    return render(request,"manager/stock/edit_paddy_stock.html",{'form':form})


@login_required
@user_passes_test(check_manager)
def delete_paddy_stock(request,id):
    paddy_stock = get_object_or_404(PaddyStockOfManager,id=id, manager=request.user)
    if request.method == "POST":
        paddy_stock.delete()
        messages.warning(request,"Paddy stock deleted successfully!")
        return redirect("paddy_stock_report")
    return redirect("paddy_stock_report")

@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def profit_loss_report_for_rice_to_manager(request):
    report_data = []
    # Find the manager who buy rice from another manager
    selling_rice_to_manager = PurchaseRice.objects.filter(
        rice__manager=request.user, status="Successful"
    ).order_by("-purchase_date")
    Owner_manager = PurchaseRice.objects.filter(
        status="Successful"
    ).order_by("-purchase_date")
   
    for selling in Owner_manager:
        selling_rice = RiceStock.objects.get(manager=selling.manager,rice_name = selling.rice.rice_name)
        for row in selling_rice_to_manager:     
            if row.manager.managerprofile.full_name == selling_rice.manager.managerprofile.full_name:
                buying_cost_per_kg = 0
                try:
                    stock = RiceStock.objects.get(manager=request.user, rice_name=row.rice.rice_name)
                    buying_cost_per_kg = stock.average_price_per_kg
                except RiceStock.DoesNotExist:
                    buying_cost_per_kg = Decimal('0.00')

                # print("buying_cost_per_kg= ",buying_cost_per_kg)
                quantity = Decimal(str(row.quantity_purchased))
                total_buying_cost = buying_cost_per_kg * quantity
                
                selling_price = Decimal(str(row.total_price)) -Decimal(str(row.delivery_cost))
                buying_price_per_kg = selling_price//quantity
                # print(buying_price_per_kg)
                selling_price_per_kg = selling_price / quantity
                profit_or_loss = selling_price - total_buying_cost
                profit_or_loss_abs = abs(profit_or_loss)
                report_data.append({
                    "row": row,
                    "cost_per_kg": buying_cost_per_kg,
                    "selling_price":selling_price,
                    "selling_price_per_kg":selling_price_per_kg,
                    "total_cost": total_buying_cost,
                    "profit_or_loss": profit_or_loss,
                    "profit_or_loss_abs": profit_or_loss_abs
                })
            
    context = {
                    "check": 1,
                    "report_data": report_data if report_data else '',
                }
    return render(request, "manager/stock/profit_loss_report.html", context)    

@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def profit_loss_report_for_rice_to_customer(request):
    # ✅ Get all successful sales made by this manager to customers
    selling_rice_to_customer = Purchase_Rice.objects.filter(
        rice__manager=request.user, status="Successful"
    ).order_by("-purchase_date")

    report_data = []

    for row in selling_rice_to_customer:
        try:
            # ✅ Get the stock record from which the manager sold this rice
            stock = RiceStock.objects.get(manager=request.user, rice_name=row.rice.rice_name)
            cost_per_kg = Decimal(str(stock.average_price_per_kg))
        except RiceStock.DoesNotExist:
            cost_per_kg = Decimal('0.00')
        # print(cost_per_kg)

        quantity = Decimal(str(row.quantity_purchased))

        total_cost = cost_per_kg * quantity
        selling_price = Decimal(str(row.total_price))-Decimal(str(row.delivery_cost))
        selling_price_per_kg = selling_price/quantity
        if row.rice.rice_name == "Amon":
            print(row.total_price)
        profit_or_loss = selling_price - total_cost
        profit_or_loss_abs = abs(profit_or_loss)

        report_data.append({
            "row": row,
            "cost_per_kg": cost_per_kg,
            "selling_price":selling_price,
            "selling_price_per_kg":selling_price_per_kg,
            "total_cost": total_cost,
            "profit_or_loss": profit_or_loss,
            "profit_or_loss_abs": profit_or_loss_abs
        })

    context = {
        "check": 2,
        "report_data": report_data,
    }

    return render(request, "manager/stock/profit_loss_report.html", context)

from django.template.loader import render_to_string
from xhtml2pdf import pisa

# helper to convert html -> pdf
def render_to_pdf(template_src, context_dict={}):
    html_string = render_to_string(template_src, context_dict)
    response = HttpResponse(content_type='application/pdf')
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response

@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def download_receipt_for_buying_paddy_for_manager(request, id):
    paddy = get_object_or_404(Purchase_paddy, id=id, manager=request.user)
    price_per_kg = float(paddy.total_price - paddy.transport_cost) // float(paddy.quantity_purchased)

    context = {
        "paddy": paddy,
        "price_per_kg": price_per_kg,
    }

    return render_to_pdf("manager/pdf_download/receipt_for_buying_paddy_pdf.html", context)

@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def download_receipt_for_buying_rice_for_manager(request, id):
    rice = get_object_or_404(PurchaseRice, id=id, manager=request.user)
    price_per_kg = float(rice.total_price - rice.delivery_cost) // float(rice.quantity_purchased)

    context = {
        "rice": rice,
        "price_per_kg": price_per_kg,
    }

    return render_to_pdf("manager/pdf_download/receipt_for_buying_rice_pdf.html", context)

@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def download_receipt_for_selling_rice_to_customer_for_manager(request, id):
    rice = get_object_or_404(Purchase_Rice, id=id, rice__manager=request.user)
    price_per_kg = float(rice.total_price - rice.delivery_cost) // float(rice.quantity_purchased)

    context = {
        "rice": rice,
        "price_per_kg": price_per_kg,
    }

    return render_to_pdf("manager/pdf_download/receipt_for_selling_to_cuatomer_rice_pdf.html", context)

@login_required(login_url="login")
@user_passes_test(check_manager_and_admin)
def download_receipt_for_selling_rice_to_others_manager_for_manager(request, id):
    rice = get_object_or_404(PurchaseRice, id=id, rice__manager=request.user)
    price_per_kg = float(rice.total_price - rice.delivery_cost) // float(rice.quantity_purchased)

    context = {
        "rice": rice,
        "price_per_kg": price_per_kg,
    }

    return render_to_pdf("manager/pdf_download/receipt_for_selling_rice_to_manager_pdf.html", context)


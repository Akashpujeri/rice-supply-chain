from django.shortcuts import get_object_or_404, redirect, render,HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from accounts.models import CustomUser
from dealer.forms import DealerProfileForm, PaddyStockForm
from dealer.models import DealerProfile, PaddyStock
from manager.models import Purchase_paddy
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import Coalesce

from django.contrib import messages
from django.db.models import Sum, Count, Avg, F, Q, Case, When, Value, FloatField
from .models import DealerProfile, Marketplace, PaddyPurchaseFromFarmer, PaddyStock
from .forms import DealerProfileEditForm, MarketplaceForm, PaddyPurchaseForm

def check_dealer(user):
    return user.is_authenticated and user.role == 'dealer'


@login_required(login_url='login')
@user_passes_test(check_dealer)
def dealer_dashboard(request):
    dealer = get_object_or_404(DealerProfile, user=request.user)

    # Get all posts by this dealer
    posts = PaddyStock.objects.filter(
        dealer=dealer,
        available_quantity__gt=0
    ).order_by('-stored_since')

    active_posts_count = posts.filter(is_available=True).count()

    total_inventory = posts.aggregate(
        total=Coalesce(Sum('available_quantity'), 0)
    )['total']

    # Use purchases to calculate real costs
    purchases = PaddyPurchaseFromFarmer.objects.filter(dealer=dealer)

    total_quantity = purchases.aggregate(total=Sum('quantity'))['total'] or 0
    total_costs = purchases.aggregate(
        total=Sum(
            F("quantity") * F("purchase_price_per_kg") +
            F("transport_cost") +
            F("other_costs"),
            output_field=FloatField()
        )
    )['total'] or 0

    avg_price = round(total_costs / total_quantity, 2) if total_quantity > 0 else 0

    # Count of recent orders (last 30 days)
    recent_orders_count = Purchase_paddy.objects.filter(
        paddy__dealer=dealer,
        purchase_date__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()

    context = {
        'dealer': dealer,
        'posts': posts,
        'active_posts_count': active_posts_count,
        
        'total_quantity': total_quantity,
        'avg_price': avg_price,
        'recent_orders_count': recent_orders_count,
    }
    return render(request, 'dealer/dashboard.html', context) 


def dealer_profile_create(request, user_id):
    user = CustomUser.objects.get(id=user_id)

    if request.method == "POST":
        form = DealerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            dealer = form.save(commit=False)
            dealer.user = user
            dealer.save()
            return redirect('login')
    else:
        form = DealerProfileForm()
    return render(request, 'dealer/dealer_profile_form.html', {'form': form})


@login_required(login_url='login')
@user_passes_test(check_dealer)
def add_paddy_post(request):
    if request.method == 'POST':
        form = PaddyStockForm(request.POST , request.FILES)
        if form.is_valid():
            paddy_post = form.save(commit=False)
            # Get dealer profile of logged-in user
            dealer = get_object_or_404(DealerProfile, user=request.user)
            paddy_post.dealer = dealer
            paddy_post.save()
            return redirect(reverse('dealer_dashboard'))  # or your desired page
    else:
        form = PaddyStockForm()
    return render(request, 'dealer/add_paddy_post.html', {'form': form})


def see_all_paddy_posts(request):
    sort = request.GET.get('sort', 'recent')
    posts = Marketplace.objects.filter(is_available=True)
    
    if sort == 'price_asc':
        posts = posts.order_by('price_per_kg')
    elif sort == 'price_desc':
        posts = posts.order_by('-price_per_kg')
    elif sort == 'moisture':
        posts = posts.order_by('moisture_content')
    else:
        posts = posts.order_by('-stored_since')


    avg_price = posts.aggregate(avg=Avg('price_per_kg'))['avg'] or 0
    total_quantity = posts.aggregate(total=Sum('quantity'))['total'] or 0
    top_dealer = posts.values('dealer__user__username').annotate(post_count=Count('id')).order_by('-post_count').first()

    return render(request, 'dealer/paddy_posts.html', {
        'posts': posts,
        'avg_price': avg_price,
        'total_quantity': total_quantity,
        'top_dealer': top_dealer['dealer__user__username'] if top_dealer else None,
        'current_sort': sort,
    })


def paddy_detail(request,post_id):
    post = get_object_or_404(Marketplace, id=post_id)
    similar_products = Marketplace.objects.filter(
        dealer=post.dealer, is_available=True
    ).exclude(id=post_id)[:4]
    
    print(similar_products)
    return render(request, 'dealer/paddy_detail.html', {
        'post': post,
        'similar_products': similar_products
    })

@login_required(login_url='login')
@user_passes_test(check_dealer, login_url='login')
def edit_paddy_post(request, post_id):
    post = get_object_or_404(PaddyStock, id=post_id)

    if request.method == 'POST':
        form = PaddyStockForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('dealer_dashboard')
    else:
        form = PaddyStockForm(instance=post)

    return render(request, 'dealer/edit_post.html', {'form': form})


@login_required(login_url='login')
@user_passes_test(check_dealer, login_url='login')
def delete_post(request, post_id):
    post = get_object_or_404(PaddyStock, id=post_id, dealer__user=request.user)

    if request.method == 'POST':
        post.delete()
        messages.success(request, f"{post.name} deleted successfully.")
        return redirect('dealer_dashboard')

    # show confirmation page
    return render(request, 'dealer/confirm_delete.html', {'post': post})


@login_required(login_url='login')
@user_passes_test(check_dealer, login_url='login')
def edit_dealer_profile(request):
    dealer_profile = request.user.dealerprofile
    print(dealer_profile)
    
    if request.method == 'POST':
        form = DealerProfileEditForm(request.POST, instance=dealer_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dealer_dashboard')
    else:
        form = DealerProfileEditForm(instance=dealer_profile)
    
    context = {
        'form': form,
        'dealer': dealer_profile
    }
    return render(request, 'dealer/edit_profile.html', context)


@login_required(login_url='login')
@user_passes_test(check_dealer, login_url='login')
def dealer_order_list(request):
    dealer = get_object_or_404(DealerProfile, user=request.user)
    orders = Purchase_paddy.objects.filter(paddy__dealer=dealer).select_related('paddy', 'manager').order_by('-purchase_date')
    
    return render(request, 'dealer/order_list.html', {'orders': orders, 'dealer': dealer})


@login_required
def dealer_stats(request):
    dealer = request.user.dealerprofile
    
    # Date ranges for statistics
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    recent_orders_count = Purchase_paddy.objects.filter(
        paddy__dealer=dealer,
        purchase_date__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    # Sales data (from Purchase_paddy)
    sales_data = Purchase_paddy.objects.filter(
        paddy__dealer=dealer,
        purchase_date__gte=last_30_days,
        is_confirmed=True
    ).extra({
        'day': "date(purchase_date)"
    }).values('day').annotate(
        total=Sum('total_price'),
        quantity=Sum('quantity_purchased')
    ).order_by('day')
    
    sales_labels = [sale['day'].strftime('%b %d') for sale in sales_data]
    sales_values = [float(sale['total']) for sale in sales_data]
    quantity_sold = [float(sale['quantity']) for sale in sales_data]
    
    # Top selling paddy varieties
    top_varieties = Purchase_paddy.objects.filter(
        paddy__dealer=dealer,
        is_confirmed=True
    ).values(
        'paddy__name'
    ).annotate(
        total_quantity=Sum('quantity_purchased'),
        total_sales=Sum('total_price'),
        count=Count('id')
    ).order_by('-total_sales')[:5]
    
    total_sales_all = sum(variety['total_sales'] for variety in top_varieties) if top_varieties else 0
    top_varieties_data = []
    top_varieties_labels = []
    
    for variety in top_varieties:
        percentage = round((variety['total_sales'] / total_sales_all) * 100) if total_sales_all > 0 else 0
        top_varieties_data.append(percentage)
        top_varieties_labels.append(variety['paddy__name'])
    
    # Purchase status breakdown
    purchase_status = Purchase_paddy.objects.filter(
        paddy__dealer=dealer
    ).aggregate(
        total=Count('id'),
        confirmed=Count('id', filter=Q(is_confirmed=True)),
        paid=Count('id', filter=Q(payment=True)),
        pending=Count('id', filter=Q(is_confirmed=False))
    )
    
    # Inventory status - simplified without Cast
    inventory_status = []
    for stock in PaddyStock.objects.filter(dealer=dealer):
        days_in_stock = (timezone.now() - stock.stored_since).days
        total_sold = Purchase_paddy.objects.filter(
            paddy=stock,
            is_confirmed=True
        ).aggregate(total=Sum('quantity_purchased'))['total'] or 0
        
        turnover_rate = days_in_stock / total_sold if total_sold > 0 else 0
        
        inventory_status.append({
            'name': stock.name,
            'stock': stock.quantity,
            'sold': total_sold,
            'turnover': round(turnover_rate, 1),
            'status': 'Low' if stock.quantity < 100 else 'Medium' if stock.quantity < 500 else 'Good',
            'moisture': stock.moisture_content,
            'price': stock.price_per_kg
        })
    
    # Calculate conversion rate
    total_stock = PaddyStock.objects.filter(dealer=dealer).aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    sold_stock = Purchase_paddy.objects.filter(
        paddy__dealer=dealer,
        is_confirmed=True
    ).aggregate(
        total=Sum('quantity_purchased')
    )['total'] or 0
    
    conversion_rate = round((sold_stock / total_stock) * 100, 1) if total_stock > 0 else 0

    print(( len(top_varieties_labels)))
    print(len(top_varieties))
    
    context = {
        'total_sales': recent_orders_count,
        'total_quantity_sold': sum(quantity_sold) if quantity_sold else 0,
        'completed_orders': purchase_status['confirmed'],
        'pending_orders': purchase_status['pending'],
        'paid_orders': purchase_status['paid'],
        'conversion_rate': conversion_rate,
        'avg_rating': dealer.average_rating() if hasattr(dealer, 'average_rating') else 4.8,
        'sales_labels': sales_labels,
        'sales_data': sales_values,
        'quantity_sold': quantity_sold,
        'top_varieties_labels': top_varieties_labels,
        'top_varieties_data': top_varieties_data,
        'top_varieties': zip(top_varieties_labels, top_varieties_data),
        'order_status_data': [
            purchase_status['confirmed'],
            purchase_status['pending'],
            purchase_status['paid'],
            purchase_status['total'] - purchase_status['confirmed']  # cancelled/rejected
        ],
        'inventory_status': inventory_status,
        'recent_purchases': Purchase_paddy.objects.filter(
            paddy__dealer=dealer
        ).select_related('manager', 'paddy').order_by('-purchase_date')[:5]
    }
    
    return render(request, 'dealer/dealer_stats.html', context)


# showing paddy selling history
@login_required
@user_passes_test(lambda u: u.role == 'dealer')
def selling_paddy_history(request):
    try:
        dealer_profile = DealerProfile.objects.get(user=request.user)
    except DealerProfile.DoesNotExist:
        return HttpResponse("Dealer profile not found", status=404)

    selling_paddy = Purchase_paddy.objects.filter(paddy__dealer=dealer_profile,status="Successful").order_by("-purchase_date")

    context = {
        "selling_paddy": selling_paddy,
    }
    return render(request, "dealer/paddy_selling_history.html", context)

# order and delivery track
@login_required
@user_passes_test(lambda u: u.role == 'dealer')
def incoming_order_for_paddy(request):
    try:
        dealer_profile = DealerProfile.objects.get(user=request.user)
    except DealerProfile.DoesNotExist:
        return HttpResponse("Dealer profile not found", status=404)
    
    orders = Purchase_paddy.objects.filter(paddy__dealer=dealer_profile).order_by("-purchase_date")
    return render(request, 'dealer/incoming_order.html', {'orders': orders})

@login_required
@user_passes_test(lambda u: u.role == 'dealer')
def accept_paddy_order(request, id):
    try:
        dealer_profile = DealerProfile.objects.get(user=request.user)
    except DealerProfile.DoesNotExist:
        return HttpResponse("Dealer profile not found", status=404)
    
    print(dealer_profile)
    order = get_object_or_404(Purchase_paddy, id=id, paddy__dealer=dealer_profile)

    if request.method == "POST":
        new_status = request.POST.get("new_status")
        print(new_status)
        if new_status in ["Accepted", "Cancel"]:
            order.status = new_status
            order.save()
    
    return redirect('incoming_order_for_paddy')

@login_required
@user_passes_test(lambda u: u.role == 'dealer')
def update_order_status_for_paddy(request, id):
    try:
        dealer_profile = DealerProfile.objects.get(user=request.user)
    except DealerProfile.DoesNotExist:
        return HttpResponse("Dealer profile not found", status=404)
    
    order = get_object_or_404(Purchase_paddy, id=id, paddy__dealer=dealer_profile)

    if request.method == "POST":
        new_status = request.POST.get('new_status')
        valid_transitions = {
            "Accepted": ["Shipping", "Cancel"],
            "Shipping": ["Delivered"],
        }
        if new_status in valid_transitions.get(order.status, []):
            order.status = new_status
            order.save()

    return redirect('incoming_order_for_paddy')


@login_required(login_url='login')
@user_passes_test(check_dealer, login_url='login')
def create_purchase(request):
    dealer = get_object_or_404(DealerProfile, user=request.user)
    if request.method == 'POST':
        form = PaddyPurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.dealer = dealer
            purchase.save()
            messages.success(request, "Purchase recorded successfully.")
            return redirect('dealer_dashboard')
    else:
        form = PaddyPurchaseForm()
    return render(request, 'dealer/purchase_form.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(check_dealer, login_url='login')
def all_purchases_list(request):
    dealer = request.user.dealerprofile
    purchases = PaddyPurchaseFromFarmer.objects.filter(dealer=dealer).order_by('-created_at')
    
    if purchases:

        context = {
            'purchases': purchases,
        }
        return render(request, 'dealer/purchases_list.html', context)
    else:
        context = {
            'purchases': "",
        }
        return render(request, 'dealer/purchases_list.html', context)
    

@login_required(login_url='login')
@user_passes_test(check_dealer, login_url='login')
def create_marketplace_post(request, id):
    dealer = request.user.dealerprofile
    paddy_stock = get_object_or_404(PaddyStock, id=id, dealer=dealer)

    if request.method == "POST":
        form = MarketplaceForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.dealer = dealer
            post.save()
            return redirect('dealer_dashboard')
    else:
        initial_data = {
            'paddy_stock': paddy_stock,
            'name': paddy_stock.name,
            'quantity': paddy_stock.available_quantity,
            'moisture_content': paddy_stock.moisture_content,
            'price_per_kg': paddy_stock.price_per_kg,
            
        }
        form = MarketplaceForm(initial=initial_data)

    return render(request, 'dealer/marketplace_form.html', {
        'form': form,
        'paddy_stock': paddy_stock  
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import PaddyPurchaseFromFarmer
from .forms import PaddyPurchaseForm

@login_required(login_url='login')
@user_passes_test(check_dealer, login_url='login')
def edit_purchase(request, pk):
    """Edit an existing purchase from farmer."""
    purchase = get_object_or_404(PaddyPurchaseFromFarmer, pk=pk, dealer=request.user.dealer)

    if request.method == "POST":
        form = PaddyPurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            messages.success(request, "Purchase updated successfully.")
            return redirect("dealer_dashboard")
        else:
            messages.error(request, "There was an error updating the purchase.")
    else:
        form = PaddyPurchaseForm(instance=purchase)

    return render(request, "dealer/edit_purchase.html", {"form": form, "purchase": purchase})

@login_required(login_url='login')
@user_passes_test(check_dealer, login_url='login')
def delete_purchase(request, pk):
    purchase = get_object_or_404(PaddyPurchaseFromFarmer, pk=pk, dealer=request.user.dealer)

    if request.method == "POST":
        purchase.delete()
        messages.success(request, "Purchase deleted successfully.")
        return redirect("dealer_dashboard")   # or your purchases list page

    # Safety: if someone tries GET
    messages.error(request, "Invalid request.")
    return redirect("dealer_dashboard")


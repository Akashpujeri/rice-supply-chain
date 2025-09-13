from .models import CustomerProfile

def customer_profile(request):
    if request.user.is_authenticated:
        try:
            customer = CustomerProfile.objects.get(user=request.user)
            return {'customer': customer}
        except CustomerProfile.DoesNotExist:
            return {}
    return {}

"""
Use a context processor to make manager available in all templates
"""
from .models import AdminProfile

def admin_profile(request):
    if request.user.is_authenticated:
        try:
            admin = AdminProfile.objects.get(user=request.user)
            return {'admin': admin}
        except AdminProfile.DoesNotExist:
            return {}
    return {}

"""
Use a context processor to make admin available in all templates
"""
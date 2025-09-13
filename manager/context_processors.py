from .models import ManagerProfile

def manager_profile(request):
    if request.user.is_authenticated:
        try:
            manager = ManagerProfile.objects.get(user=request.user)
            return {'manager': manager}
        except ManagerProfile.DoesNotExist:
            return {}
    return {}

"""
Use a context processor to make manager available in all templates
"""
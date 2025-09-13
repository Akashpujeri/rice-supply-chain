from django import forms
from .models import AdminProfile
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
User = get_user_model()

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ['full_name','phone_number','license_number','address','bio','profile_image']

        widgets = {
            'full_name':forms.TextInput(attrs={'class':'form-control'}),
            'phone_number': forms.TextInput(attrs={'class':'form-control'}),
            'address': forms.Textarea(attrs={'class':'form-control'}),
            'license_number': forms.TextInput(attrs={'class':'form-control'}),
            'bio': forms.Textarea(attrs={'class':'form-control'}),
            'profile_image': forms.ClearableFileInput(attrs={'class':'form-control'}),
        }


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Old Password'})
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter New Password'})
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'})
    )
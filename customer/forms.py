from django import forms

from .models import CustomerProfile, Purchase_Rice, Payment_For_Rice

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['full_name', 'phone_number','Transaction_password', 'address', 'image', 'date_of_birth']
        widgets = {
        'full_name': forms.TextInput(attrs={'class': 'form-control'}),
        'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        'Transaction_password': forms.TextInput(attrs={'class': 'form-control'}),
        'address': forms.Textarea(attrs={'class': 'form-control'}),
        'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class PaymentForRiceForm(forms.ModelForm):
    class Meta:
        model = Payment_For_Rice
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PurchaseRiceForm(forms.ModelForm):
    class Meta:
        model = Purchase_Rice
        fields = ['quantity_purchased','delivery_cost']
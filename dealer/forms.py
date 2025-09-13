from django import forms
from django.core.exceptions import ValidationError
from .models import DealerProfile, Marketplace, PaddyPurchaseFromFarmer, PaddyStock

class PaddyStockForm(forms.ModelForm):
    class Meta:
        model = PaddyStock
        exclude = ['dealer', 'stored_since']  # system-controlled fields
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Paddy Name'}),
            'moisture_category': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'transport_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'other_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'moisture_content': forms.NumberInput(attrs={'class': 'form-control', 'min': '5', 'max': '25', 'step': '0.1'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'quality_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter any quality notes...'}),
        }

class DealerProfileForm(forms.ModelForm):
    class Meta:
        model = DealerProfile
        exclude = ['user']   # user will be set programmatically
        widgets = {
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'taluk': forms.TextInput(attrs={'class': 'form-control'}),
            'village_or_city': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[1-9][0-9]{5}',  # Indian 6-digit pincode
                'title': 'Enter a valid 6-digit Indian pincode'
            }),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DealerProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = DealerProfile
        fields = [
            'first_name', 'last_name', 'email',
            'license_number', 'storage_capacity',
            'state', 'district', 'taluk',
            'village_or_city', 'pincode', 'address'
        ]
        widgets = {
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'taluk': forms.TextInput(attrs={'class': 'form-control'}),
            'village_or_city': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[1-9][0-9]{5}',  
                'title': 'Enter a valid 6-digit Indian pincode'
            }),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user'):
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        dealer = super().save(commit=False)
        if commit:
            dealer.user.first_name = self.cleaned_data['first_name']
            dealer.user.last_name = self.cleaned_data['last_name']
            dealer.user.email = self.cleaned_data['email']
            dealer.user.save()
            dealer.save()
        return dealer


class PaddyPurchaseForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1'}),
        label='Quantity (Kg)'
    )

    class Meta:
        model = PaddyPurchaseFromFarmer
        fields = [
            'farmer_name', 'farmer_phone', 'paddy_type', 'quantity',
            'purchase_price_per_kg', 'moisture_content',
            'transport_cost', 'other_costs', 'notes'
        ]
        widgets = {
            'farmer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'farmer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'paddy_type': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('Sona Masoori', 'Sona Masoori'),
                ('Basmati', 'Basmati'),
                ('IR64', 'IR64'),
                ('Swarna', 'Swarna'),
                ('Local', 'Local Variety'),

            ]),
            'purchase_price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'moisture_content': forms.NumberInput(attrs={'class': 'form-control', 'min': '5', 'max': '25', 'step': '0.1'}),
            'transport_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'other_costs': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'purchase_price_per_kg': 'Price per Kg (₹)',
            'moisture_content': 'Moisture Content (%)'
        }
        help_texts = {
            'moisture_content': 'Measure with moisture meter (12–14% ideal)',
            'farmer_phone': 'Indian mobile number (10 digits, starts with 6/7/8/9)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mobile number validation pattern for India
        self.fields['farmer_phone'].widget.attrs.update({
            'pattern': '[6-9]{1}[0-9]{9}',
            'title': 'Please enter a valid 10-digit Indian mobile number'
        })

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is None or qty < 1:
            raise forms.ValidationError("Minimum purchase quantity is 1 Kg")
        return qty

    def clean_moisture_content(self):
        moisture = self.cleaned_data.get('moisture_content')
        if moisture is None or not (5 <= moisture <= 25):
            raise forms.ValidationError("Moisture content must be between 5% and 25%")
        return round(moisture, 1)

    def clean_farmer_phone(self):
        phone = self.cleaned_data.get('farmer_phone')
        if phone:
            if not phone.isdigit() or len(phone) != 10 or phone[0] not in ['6', '7', '8', '9']:
                raise forms.ValidationError(
                    "Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9"
                )
        return phone


class MarketplaceForm(forms.ModelForm):
    class Meta:
        model = Marketplace
        fields = [
            'paddy_stock', 'name', 'image',
            'quantity', 'moisture_content',
            'price_per_kg', 'quality_notes', 'status'
        ]
        widgets = {
            'paddy_stock': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1'}),
            'moisture_content': forms.NumberInput(attrs={'class': 'form-control', 'min': '5', 'max': '25', 'step': '0.1'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'quality_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'quantity': 'Quantity (Kg)',
            'price_per_kg': 'Price per Kg (₹)',
            'moisture_content': 'Moisture Content (%)',
        }
        help_texts = {
            'quantity': 'Enter quantity in Kg (should not exceed available stock)',
            'price_per_kg': 'Set selling price in ₹ per Kg',
        }

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        stock = self.cleaned_data.get('paddy_stock')

        if stock and qty > stock.available_quantity:
            raise forms.ValidationError(f"Cannot list more than available stock ({stock.available_quantity} Kg)")
        return qty

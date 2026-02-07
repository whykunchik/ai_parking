from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CarOwner, VehicleRequest

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=11, required=True, label='Телефон')
    first_name = forms.CharField(max_length=50, required=True, label='Имя')
    last_name = forms.CharField(max_length=50, required=True, label='Фамилия')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            CarOwner.objects.create(
                user=user,
                phone=self.cleaned_data['phone']
            )
        return user

class VehicleRequestForm(forms.ModelForm):
    class Meta:
        model = VehicleRequest
        fields = ['state_number', 'brand', 'model', 'color', 'year', 'vehicle_type']
        widgets = {
            'state_number': forms.TextInput(attrs={
                'placeholder': 'А123БВ77',
                'class': 'form-control'
            }),
            'brand': forms.TextInput(attrs={
                'placeholder': 'Toyota',
                'class': 'form-control'
            }),
            'model': forms.TextInput(attrs={
                'placeholder': 'Camry',
                'class': 'form-control'
            }),
            'color': forms.TextInput(attrs={
                'placeholder': 'Черный',
                'class': 'form-control'
            }),
            'year': forms.NumberInput(attrs={
                'placeholder': '2020',
                'class': 'form-control',
                'min': '1900',
                'max': '2100'
            }),
            'vehicle_type': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем CSS классы ко всем полям
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
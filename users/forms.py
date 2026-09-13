from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Име",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Фамилия",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'})
    )
    email = forms.EmailField(
        required=True,
        label="Имейл адрес",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    avatar = forms.ImageField(
        required=True,
        label="Профилна снимка",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Телефон за връзка",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08XXXXXXXX'})
    )
    car_model = forms.CharField(
        max_length=100,
        required=True,
        label="Автомобил (Марка/Модел)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'напр. Mercedes S 63'})
    )
    facebook_url = forms.URLField(
        required=False,
        label="Facebook профил (по желание)",
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/your.profile'})
    )
    instagram_url = forms.URLField(
        required=False,
        label="Instagram профил (по желание)",
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/your.username'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'potrebitel123'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Потребителско име',
            'first_name': 'Име',
            'last_name': 'Фамилия',
            'email': 'Имейл адрес',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control form-control-gt'


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'phone_number', 'car_model', 'bio', 'facebook_url', 'instagram_url']
        labels = {
            'avatar': 'Профилна снимка',
            'phone_number': 'Телефонен номер',
            'car_model': 'Автомобил (Марка и модел)',
            'bio': 'За мен',
            'facebook_url': 'Facebook профил (по желание)',
            'instagram_url': 'Instagram профил (по желание)',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'placeholder': 'https://facebook.com/vashiat.profil'}),
            'instagram_url': forms.URLInput(attrs={'placeholder': 'https://instagram.com/vashiat.profil'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].required = False
        self.fields['phone_number'].required = True
        self.fields['car_model'].required = True
        self.fields['bio'].required = True

        self.fields['facebook_url'].required = False
        self.fields['instagram_url'].required = False
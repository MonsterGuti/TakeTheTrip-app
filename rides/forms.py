from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Ride

User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Име')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    email = forms.EmailField(required=True, label='Имейл адрес')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': 'Потребителско име',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control form-control-gt'


class RideForm(forms.ModelForm):
    class Meta:
        model = Ride
        fields = [
            'origin',
            'destination',
            'departure_time',
            'available_seats',
            'price_per_seat',
        ]
        labels = {
            'origin': 'От град/село',
            'destination': 'До град/село',
            'departure_time': 'Дата и час на тръгване',
            'available_seats': 'Брой свободни места',
            'price_per_seat': 'Цена на място (€)',
        }
        widgets = {
            'origin': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-gt',
                    'placeholder': 'напр. София',
                }
            ),
            'destination': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-gt',
                    'placeholder': 'напр. Пловдив',
                }
            ),
            'departure_time': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',  # Ключово за Android Chrome
                attrs={
                    'class': 'form-control form-control-gt',
                    'type': 'datetime-local',
                    'onclick': 'this.showPicker()',  # Отваря директно системния календар при натискане
                }
            ),
            'available_seats': forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-gt',
                    'min': 1,
                    'max': 8,
                }
            ),
            'price_per_seat': forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-gt',
                    'step': '0.50',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['departure_time'].widget.format = '%Y-%m-%dT%H:%M'

from .models import RideMessage

class RideMessageForm(forms.ModelForm):
    class Meta:
        model = RideMessage
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'form-control form-control-gt',
                'placeholder': 'Напишете съобщение до групата...',
                'autocomplete': 'off'
            }),
        }
        labels = {
            'content': ''
        }
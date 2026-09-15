from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    avatar = models.ImageField(
        upload_to='profile_pics/',
        blank=False,
        null=False,
        verbose_name='Профилна снимка',
    )
    phone_number = models.CharField(
        max_length=20,
        blank=False,
        null=False,
        verbose_name='Телефонен номер'
    )
    car_model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Автомобил (Марка и модел)',
        help_text='напр. Mercedes-Benz S 63',
    )
    bio = models.TextField(
        max_length=500,
        blank=False,
        null=False,
        verbose_name='За мен',
        help_text='Кратко описание за теб като шофьор или пътник',
    )

    facebook_url = models.URLField(max_length=255, blank=True, null=True, verbose_name="Facebook профил")
    instagram_url = models.URLField(max_length=255, blank=True, null=True, verbose_name="Instagram профил")

    def __str__(self):
        return f'Профил на {self.user.username}'
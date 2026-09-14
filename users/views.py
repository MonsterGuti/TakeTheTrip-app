import base64
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.conf import settings
from django.core.mail import send_mail
from django.core.files.base import ContentFile
from django.utils.html import strip_tags

from rides.models import Ride
from reviews.models import Review
from .models import Profile
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm

User = get_user_model()


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            profile, created = Profile.objects.get_or_create(user=user)

            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            profile.phone_number = form.cleaned_data.get('phone_number')
            profile.car_model = form.cleaned_data.get('car_model')
            profile.facebook_url = form.cleaned_data.get('facebook_url')
            profile.instagram_url = form.cleaned_data.get('instagram_url')
            profile.save()

            login(request, user)

            if user.email:
                pass

            messages.success(request, f'Успешна регистрация! Добре дошли, {user.username}!')
            return redirect('home')
    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=profile_obj
        )

        cropped_avatar = request.POST.get('cropped_avatar')

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            updated_profile = p_form.save(commit=False)

            # Обработка на изрязаното изображение от Cropper.js (Base64)
            if cropped_avatar:
                format, imgstr = cropped_avatar.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f'avatar_{request.user.id}.{ext}')
                updated_profile.avatar = data

            updated_profile.save()
            messages.success(request, 'Профилът ви беше обновен успешно!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile_obj)

    driver_rides = Ride.objects.filter(driver=request.user).order_by('-departure_time')
    reviews = Review.objects.filter(driver=request.user).select_related('reviewer', 'reviewer__profile').order_by(
        '-created_at')
    avg_rating_val = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating_val, 1)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'user_obj': request.user,
        'is_own_profile': True,
        'driver_rides': driver_rides,
        'reviews': reviews,
        'avg_rating': avg_rating,
    }
    return render(request, 'users/profile.html', context)


def public_profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    if request.user == profile_user:
        return redirect('profile')

    Profile.objects.get_or_create(user=profile_user)
    driver_rides = Ride.objects.filter(driver=profile_user).order_by('-departure_time')

    reviews = Review.objects.filter(driver=profile_user).select_related('reviewer', 'reviewer__profile').order_by(
        '-created_at')
    avg_rating_val = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating_val, 1)

    context = {
        'profile_user': profile_user,
        'user_obj': profile_user,
        'is_own_profile': False,
        'driver_rides': driver_rides,
        'reviews': reviews,
        'avg_rating': avg_rating,
    }
    return render(request, 'users/profile.html', context)
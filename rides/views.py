import threading
from datetime import datetime
import os
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from .models import Ride, Booking, RideMessage
from .forms import RideForm, RegisterForm, RideMessageForm
from notifications.models import Notification

User = get_user_model()


def get_user_display_name(user):
    if hasattr(user, 'display_name') and user.display_name:
        return user.display_name
    full_name = user.get_full_name()
    return full_name if full_name else user.username


def create_system_chat_message(ride, text):
    RideMessage.objects.create(
        ride=ride,
        sender=ride.driver,
        content=f"🤖 [Система]: {text}"
    )


def send_notification_email(recipient, subject, message, action_url=None):
    """Имейл функционалността е временно изключена."""
    pass


def home(request):
    origin = request.GET.get('origin', '').strip()
    destination = request.GET.get('destination', '').strip()
    date_str = request.GET.get('date', '').strip()

    rides = Ride.objects.filter(
        available_seats__gt=0,
        departure_time__gte=timezone.now()
    ).select_related('driver').order_by('departure_time')

    if origin:
        rides = rides.filter(origin__icontains=origin)
    if destination:
        rides = rides.filter(destination__icontains=destination)
    if date_str:
        try:
            search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            rides = rides.filter(departure_time__date=search_date)
        except ValueError:
            pass

    return render(request, 'rides/home.html', {
        'rides': rides,
        'origin_query': origin,
        'destination_query': destination,
        'date_query': date_str,
    })


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Неактивен до потвърждаване на имейла
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            activation_link = reverse('activate', kwargs={'uidb64': uid, 'token': token})

            subject = "Потвърждение на профила ви в TakeTheTrip"
            email_body = "Благодарим ви за регистрацията! Моля, потвърдете вашия имейл адрес, за да активирате профила си и да използвате услугата."

            send_notification_email(
                recipient=user,
                subject=subject,
                message=email_body,
                action_url=activation_link
            )

            messages.info(request, 'Регистрацията е успешна! Изпратихме ви имейл с линк за активация на профила.')
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, "Профилът ви беше потвърден и активиран успешно!")
        return redirect('home')
    else:
        messages.error(request, "Линкът за потвърждение е невалиден или изтекъл!")
        return redirect('login')


def ride_detail(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    user_booking = None
    has_confirmed_booking = False

    if request.user.is_authenticated:
        user_booking = Booking.objects.filter(
            ride=ride,
            passenger=request.user,
            status__in=['PENDING', 'APPROVED', 'CONFIRMED', 'pending', 'approved', 'confirmed']
        ).first()

        if not user_booking:
            user_booking = Booking.objects.filter(
                ride=ride,
                passenger=request.user
            ).order_by('-id').first()

        if user_booking and user_booking.status:
            status_upper = str(user_booking.status).upper()
            if status_upper in ['APPROVED', 'CONFIRMED']:
                has_confirmed_booking = True

    is_driver = request.user.is_authenticated and request.user == ride.driver
    is_participant = is_driver or has_confirmed_booking

    if request.method == 'POST' and is_participant:
        message_form = RideMessageForm(request.POST)
        if message_form.is_valid():
            msg = message_form.save(commit=False)
            msg.ride = ride
            msg.sender = request.user
            msg.save()
            return redirect('ride_detail', pk=pk)
    else:
        message_form = RideMessageForm()

    bookings = Booking.objects.filter(ride=ride).select_related('passenger')
    messages_list = ride.messages.select_related('sender').all() if is_participant else []

    return render(request, 'rides/ride_detail.html', {
        'ride': ride,
        'user_booking': user_booking,
        'has_confirmed_booking': has_confirmed_booking,
        'is_driver': is_driver,
        'is_participant': is_participant,
        'bookings': bookings,
        'messages_list': messages_list,
        'message_form': message_form
    })


@login_required
def book_ride(request, pk):
    ride = get_object_or_404(Ride, id=pk)

    if ride.driver == request.user:
        messages.error(request, "Не можете да резервирате собственoто си пътуване!")
        return redirect(f"{reverse('ride_detail', kwargs={'pk': ride.id})}#participants-section")

    existing_booking = Booking.objects.filter(
        ride=ride,
        passenger=request.user,
        status__in=['PENDING', 'APPROVED', 'pending', 'approved', 'confirmed']
    ).first()

    if existing_booking:
        messages.warning(request, "Вече имате активна заявка или резервация за това пътуване.")
        return redirect(f"{reverse('ride_detail', kwargs={'pk': ride.id})}#participants-section")

    if request.method == 'POST':
        booking = Booking.objects.create(
            ride=ride,
            passenger=request.user,
            status='PENDING'
        )

        msg_text = f"{get_user_display_name(request.user)} изпрати заявка за пътуването до {ride.destination}."

        Notification.objects.create(
            recipient=ride.driver,
            sender=request.user,
            notification_type='booking_request',
            ride=ride,
            message=msg_text
        )

        subject = f"Нова заявка за вашето пътуване: {ride.origin} ➔ {ride.destination}"
        email_body = f"Потребителят {get_user_display_name(request.user)} изпрати заявка за резервация за пътуването ви от {ride.origin} до {ride.destination}."
        ride_url = reverse('ride_detail', kwargs={'pk': ride.id})

        send_notification_email(
            recipient=ride.driver,
            subject=subject,
            message=email_body,
            action_url=f"{ride_url}#participants-section"
        )

        messages.success(request, "Заявката за резервация беше изпратена успешно!")
        return redirect(f"{reverse('ride_detail', kwargs={'pk': ride.id})}#participants-section")

    return redirect(f"{reverse('ride_detail', kwargs={'pk': ride.id})}#participants-section")


@login_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, ride__driver=request.user)

    if booking.status in ['PENDING', 'pending']:
        booking.status = 'APPROVED'
        booking.save()

        booking.ride.available_seats -= booking.seats_booked
        booking.ride.save()

        passenger_name = get_user_display_name(booking.passenger)
        create_system_chat_message(booking.ride, f"{passenger_name} се присъедини към пътуването!")

        Notification.objects.create(
            recipient=booking.passenger,
            sender=request.user,
            notification_type='booking_response',
            ride=booking.ride,
            message=f"Заявката ви за {booking.ride.origin} ➔ {booking.ride.destination} беше ОДОБРЕНА!"
        )

        subject = f"Одобрена резервация: {booking.ride.origin} ➔ {booking.ride.destination}"
        email_body = (
            f"Шофьорът {get_user_display_name(booking.ride.driver)} одобри вашата заявка за пътуване "
            f"от {booking.ride.origin} до {booking.ride.destination} "
            f"на {booking.ride.departure_time.strftime('%d.%m.%Y в %H:%M ч.')}."
        )
        ride_url = reverse('ride_detail', kwargs={'pk': booking.ride.pk})

        send_notification_email(
            recipient=booking.passenger,
            subject=subject,
            message=email_body,
            action_url=ride_url
        )

        messages.success(request, f"Заявката на {passenger_name} беше одобрена и имейлът е изпратен!")

    return redirect(f"{reverse('ride_detail', kwargs={'pk': booking.ride.pk})}#participants-section")


@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, ride__driver=request.user)

    if booking.status in ['PENDING', 'pending']:
        booking.status = 'REJECTED'
        booking.save()

        passenger_name = get_user_display_name(booking.passenger)

        Notification.objects.create(
            recipient=booking.passenger,
            sender=request.user,
            notification_type='cancellation',
            ride=booking.ride,
            message=f"Заявката ви за резервация за {booking.ride.origin} ➔ {booking.ride.destination} беше отклонена."
        )

        subject = f"Заявката ви бе отхвърлена: {booking.ride.origin} ➔ {booking.ride.destination}"
        email_body = f"За съжаление шофьорът не можа да потвърди заявката ви за пътуването от {booking.ride.origin} до {booking.ride.destination}."
        ride_url = reverse('ride_detail', kwargs={'pk': booking.ride.pk})

        send_notification_email(
            recipient=booking.passenger,
            subject=subject,
            message=email_body,
            action_url=ride_url
        )

        messages.info(request, f"Заявката на {passenger_name} беше отклонена.")

    return redirect(f"{reverse('ride_detail', kwargs={'pk': booking.ride.pk})}#participants-section")


@login_required
def remove_passenger(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, ride__driver=request.user)

    if booking.status in ['APPROVED', 'approved', 'confirmed', 'PENDING', 'pending']:
        was_approved = booking.status in ['APPROVED', 'approved', 'confirmed']

        booking.status = 'REJECTED'
        booking.save()

        if was_approved:
            booking.ride.available_seats += booking.seats_booked
            booking.ride.save()

        passenger_name = get_user_display_name(booking.passenger)
        create_system_chat_message(booking.ride, f"{passenger_name} беше премахнат от пътуването.")

        Notification.objects.create(
            recipient=booking.passenger,
            sender=request.user,
            notification_type='cancellation',
            ride=booking.ride,
            message=f"Беше премахнат от пътуването {booking.ride.origin} ➔ {booking.ride.destination} от шофьора."
        )

        subject = f"Промяна по резервацията: {booking.ride.origin} ➔ {booking.ride.destination}"
        email_body = f"Шофьорът ви премахна от пътуването от {booking.ride.origin} до {booking.ride.destination}."
        ride_url = reverse('ride_detail', kwargs={'pk': booking.ride.pk})

        send_notification_email(
            recipient=booking.passenger,
            subject=subject,
            message=email_body,
            action_url=ride_url
        )

        messages.info(request, f"Пътникът {passenger_name} беше премахнат от пътуването.")

    return redirect(f"{reverse('ride_detail', kwargs={'pk': booking.ride.pk})}#participants-section")


@login_required
def cancel_booking(request, pk):
    ride = get_object_or_404(Ride, pk=pk)

    booking = Booking.objects.filter(
        ride=ride,
        passenger=request.user,
        status__in=['PENDING', 'APPROVED', 'pending', 'approved', 'confirmed']
    ).first()

    if booking:
        old_status = str(booking.status).upper()
        booking.status = 'CANCELLED'
        booking.save()

        if old_status in ['APPROVED', 'CONFIRMED']:
            ride.available_seats += booking.seats_booked
            ride.save()

        passenger_name = get_user_display_name(request.user)
        create_system_chat_message(ride, f"{passenger_name} се отказа от пътуването.")

        Notification.objects.create(
            recipient=ride.driver,
            sender=request.user,
            notification_type='cancellation',
            ride=ride,
            message=f"{passenger_name} отказа резервацията си за {ride.origin} ➔ {ride.destination}."
        )

        subject = f"Отказ от резервация: {ride.origin} ➔ {ride.destination}"
        email_body = f"Пътникът {passenger_name} отказа своята резервация за пътуването ви от {ride.origin} до {ride.destination}."
        ride_url = reverse('ride_detail', kwargs={'pk': ride.id})

        send_notification_email(
            recipient=ride.driver,
            subject=subject,
            message=email_body,
            action_url=f"{ride_url}#participants-section"
        )

        messages.info(request, "Успешно се отказахте от пътуването.")
    else:
        messages.error(request, "Нямате активна резервация за това пътуване.")

    return redirect(f"{reverse('ride_detail', kwargs={'pk': pk})}#participants-section")


@login_required
def create_ride(request):
    if request.method == 'POST':
        form = RideForm(request.POST)
        if form.is_valid():
            ride = form.save(commit=False)
            ride.driver = request.user
            ride.save()
            return redirect('home')
    else:
        form = RideForm()

    return render(request, 'rides/create_ride.html', {'form': form})


@login_required
def edit_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk, driver=request.user)

    if request.method == 'POST':
        form = RideForm(request.POST, instance=ride)
        if form.is_valid():
            form.save()

            confirmed_bookings = Booking.objects.filter(
                ride=ride,
                status__in=['APPROVED', 'approved', 'confirmed', 'CONFIRMED']
            ).select_related('passenger')

            driver_name = get_user_display_name(request.user)
            ride_url = reverse('ride_detail', kwargs={'pk': ride.pk})

            for b in confirmed_bookings:
                Notification.objects.create(
                    recipient=b.passenger,
                    sender=request.user,
                    notification_type='update',
                    ride=ride,
                    message=f"Шофьорът {driver_name} актуализира детайлите за пътуването от {ride.origin} до {ride.destination}."
                )

                subject = f"Промяна в пътуването: {ride.origin} ➔ {ride.destination}"
                email_body = f"Шофьорът {driver_name} актуализира детайлите за пътуването от {ride.origin} до {ride.destination}. Моля, прегледайте новата информация."

                send_notification_email(
                    recipient=b.passenger,
                    subject=subject,
                    message=email_body,
                    action_url=ride_url
                )

            messages.success(request, 'Пътуването беше обновено успешно!')
            return redirect('ride_detail', pk=ride.pk)
    else:
        form = RideForm(instance=ride)

    return render(request, 'rides/edit_ride.html', {'form': form, 'ride': ride})


@login_required
def delete_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk)

    if ride.driver != request.user:
        messages.error(request, "Нямате разрешение да изтриете това пътуване!")
        return redirect('ride_detail', pk=pk)

    if request.method == 'POST':
        confirmed_bookings = Booking.objects.filter(
            ride=ride,
            status__in=['APPROVED', 'approved', 'confirmed', 'CONFIRMED']
        ).select_related('passenger')

        driver_name = get_user_display_name(request.user)
        departure_str = ride.departure_time.strftime('%d.%m.%Y в %H:%M ч.')

        for b in confirmed_bookings:
            Notification.objects.create(
                recipient=b.passenger,
                sender=request.user,
                notification_type='cancellation',
                ride=None,
                message=f"Пътуването от {ride.origin} до {ride.destination} ({departure_str}) беше отменено от шофьора."
            )

            subject = f"Отменено пътуване: {ride.origin} ➔ {ride.destination}"
            email_body = f"Шофьорът {driver_name} отмени пътуването от {ride.origin} до {ride.destination}, насрочено за {departure_str}."

            send_notification_email(
                recipient=b.passenger,
                subject=subject,
                message=email_body,
                action_url=reverse('home')
            )

        ride.delete()
        messages.success(request, "Пътуването беше изтрито успешно.")
        return redirect('my_rides')

    return redirect('ride_detail', pk=pk)


@login_required
@require_POST
def send_message_ajax(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    has_confirmed = Booking.objects.filter(ride=ride, passenger=request.user,
                                           status__in=['APPROVED', 'approved', 'confirmed']).exists()
    is_driver = request.user == ride.driver

    if not (is_driver or has_confirmed):
        return JsonResponse({'success': False, 'error': 'Нямате достъп.'}, status=403)

    form = RideMessageForm(request.POST)
    if form.is_valid():
        msg = form.save(commit=False)
        msg.ride = ride
        msg.sender = request.user
        msg.save()

        sender_name = get_user_display_name(request.user)

        recipients_ids = set()
        if is_driver:
            passengers = Booking.objects.filter(ride=ride,
                                                status__in=['APPROVED', 'approved', 'confirmed']).values_list(
                'passenger_id', flat=True)
            recipients_ids.update(passengers)
        else:
            recipients_ids.add(ride.driver.id)

        recipients_ids.discard(request.user.id)

        notifications_to_create = [
            Notification(
                recipient_id=user_id,
                sender=request.user,
                notification_type='chat',
                ride=ride,
                message=f"Ново съобщение от {sender_name} за {ride.origin} ➔ {ride.destination}."
            ) for user_id in recipients_ids
        ]
        Notification.objects.bulk_create(notifications_to_create)

        avatar_url = None
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'avatar') and request.user.profile.avatar:
            avatar_url = request.user.profile.avatar.url

        return JsonResponse({
            'success': True,
            'sender': sender_name,
            'sender_initial': request.user.username[0].upper() if request.user.username else '',
            'avatar_url': avatar_url,
            'content': msg.content,
            'time': msg.created_at.strftime('%H:%M')
        })

    return JsonResponse({'success': False, 'error': 'Невалидно съобщение.'}, status=400)


@login_required
def get_messages_ajax(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    has_confirmed = Booking.objects.filter(ride=ride, passenger=request.user,
                                           status__in=['APPROVED', 'approved', 'confirmed']).exists()
    is_driver = request.user == ride.driver

    if not (is_driver or has_confirmed):
        return JsonResponse({'success': False, 'error': 'Нямате достъп.'}, status=403)

    messages_qs = ride.messages.select_related('sender').all()
    messages_data = []

    for msg in messages_qs:
        avatar_url = None
        if hasattr(msg.sender, 'profile') and hasattr(msg.sender.profile, 'avatar') and msg.sender.profile.avatar:
            avatar_url = msg.sender.profile.avatar.url

        sender_name = get_user_display_name(msg.sender)

        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_username': msg.sender.username,
            'sender_name': sender_name,
            'sender_initial': msg.sender.username[0].upper() if msg.sender.username else '',
            'avatar_url': avatar_url,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%H:%M'),
            'is_me': msg.sender == request.user
        })

    return JsonResponse({'success': True, 'messages': messages_data})


@login_required
def my_rides(request):
    now = timezone.now()

    driver_upcoming = Ride.objects.filter(
        driver=request.user,
        departure_time__gte=now
    ).order_by('departure_time')

    driver_past = Ride.objects.filter(
        driver=request.user,
        departure_time__lt=now
    ).order_by('-departure_time')

    passenger_upcoming = Booking.objects.filter(
        passenger=request.user,
        ride__departure_time__gte=now
    ).exclude(
        status__in=['REJECTED', 'rejected', 'CANCELLED', 'cancelled']
    ).select_related('ride', 'ride__driver').order_by('ride__departure_time').distinct()

    passenger_past = Booking.objects.filter(
        passenger=request.user,
        ride__departure_time__lt=now
    ).exclude(
        status__in=['REJECTED', 'rejected', 'CANCELLED', 'cancelled']
    ).select_related('ride', 'ride__driver').order_by('-ride__departure_time').distinct()

    return render(request, 'rides/my_rides.html', {
        'driver_upcoming': driver_upcoming,
        'driver_past': driver_past,
        'passenger_upcoming': passenger_upcoming,
        'passenger_past': passenger_past,
    })


import requests


def proxy_geocode(request):
    city = request.GET.get('q', '').strip()
    if not city:
        return JsonResponse({'error': 'No city provided'}, status=400)

    headers = {'User-Agent': 'TakeTheTripApp/1.0 (contact@takethetripapp.com)'}

    url = f"https://nominatim.openstreetmap.org/search?format=json&city={city}&country=Bulgaria&limit=1"

    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()

        if not data:
            url_fallback = f"https://nominatim.openstreetmap.org/search?format=json&q={city},Bulgaria&limit=5"
            response = requests.get(url_fallback, headers=headers, timeout=5)
            results = response.json()

            for item in results:
                place_type = item.get('type', '')
                if place_type in ['city', 'town', 'village', 'administrative'] and item.get('class') == 'boundary':
                    continue
                data = [item]
                break
            if not data and results:
                data = [results[0]]

        if data:
            return JsonResponse({'lon': float(data[0]['lon']), 'lat': float(data[0]['lat'])})
    except Exception as e:
        pass

    return JsonResponse({'error': 'Not found'}, status=404)
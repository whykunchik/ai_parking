from django.shortcuts import render, redirect, get_object_or_404
# render - рендеринг шаблона
# redirect - перенаправление на другой URL
# get_object_or_404 - получить объект или вернуть 404

from django.contrib.auth.decorators import login_required
# login_required - декоратор для защиты view (требует аутентификации)

from django.contrib.auth import login, authenticate
# login - функция для входа пользователя
# authenticate - проверка логина/пароля

from django.contrib.auth.forms import AuthenticationForm
# AuthenticationForm - стандартная форма аутентификации Django

from django.contrib import messages
# messages - система flash-сообщений

from catalog.models import CarOwner, Vehicle, ParkingSession, Payment, Tariff
# Импорт моделей из приложения catalog

from django.db.models import Sum

from datetime import datetime, timedelta
# datetime - работа с датой/временем
# timedelta - разница во времени
from .forms import UserRegistrationForm 
# Импортируем форму
from django.contrib.auth import logout as auth_logout

from catalog.models import CarOwner, Vehicle, ParkingSession, Payment, LicensePlateDetection

# Функция входа
def login_view(request):
    # Если POST-запрос (пользователь отправил форму)
    if request.method == 'POST':
        # Создаем форму с данными из POST
        form = AuthenticationForm(request, data=request.POST)
        
        # Проверяем валидность формы
        if form.is_valid():
            # Извлекаем очищенные данные
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Аутентифицируем пользователя
            user = authenticate(username=username, password=password)
            
            # Если пользователь существует
            if user is not None:
                # Входим в пользователя (создает сессию)
                login(request, user)
                
                # Добавляем сообщение об успехе
                messages.success(request, f"Добро пожаловать, {username}!")
                
                # Проверяем, является ли пользователь администратором
                if user.is_staff:
                    return redirect('admin_dashboard')  # Перенаправляем админа
                else:
                    return redirect('dashboard')  # Перенаправляем обычного пользователя
            else:
                messages.error(request, "Неверное имя пользователя или пароль.")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    
    # Если GET-запрос или ошибка - показываем пустую форму
    form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})
 
@login_required
def user_dashboard_view(request):
    """Панель управления для обычных пользователей"""
    user = request.user
    context = {
        'user': user,
        'full_name': user.get_full_name() or user.username,
    }
    return render(request, 'users/dashboard.html', context)

@login_required
def admin_dashboard_view(request):
    """Панель управления для администраторов"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    # Статистика для админ-панели
    today = datetime.now().date()
    
    context = {
        'user': request.user,
        'today': today,
        'total_parking_sessions': ParkingSession.objects.count(),
        'active_sessions': ParkingSession.objects.filter(exit_time__isnull=True).count(),
        'total_revenue': Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'today_sessions': ParkingSession.objects.filter(
            entry_time__date=today
        ).count(),
    }
    
    return render(request, 'admin/dashboard.html', context)

def register_view(request):
    """Представление для регистрации пользователя"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически входим после регистрации
            messages.success(request, f'Аккаунт создан для {user.username}!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def my_vehicles_view(request):
    """Страница с автомобилями пользователя"""
    try:
        # Получаем CarOwner текущего пользователя
        car_owner = CarOwner.objects.get(user=request.user)
        vehicles = Vehicle.objects.filter(owner=car_owner)
        vehicle_count = vehicles.count()
    except CarOwner.DoesNotExist:
        vehicles = []
        car_owner = None
        vehicle_count = 0
    
    from datetime import datetime
    current_time = datetime.now()
    
    context = {
        'vehicles': vehicles,
        'car_owner': car_owner,
        'vehicle_count': vehicle_count,
        'current_time': current_time,
    }
    return render(request, 'users/my_vehicles.html', context)

@login_required
def parking_sessions_view(request):
    """Страница с парковочными сессиями пользователя"""
    try:
        car_owner = CarOwner.objects.get(user=request.user)
        # Получаем все автомобили пользователя
        user_vehicles = Vehicle.objects.filter(owner=car_owner)
        # Получаем парковочные сессии для этих автомобилей
        parking_sessions = ParkingSession.objects.filter(
            vehicle__in=user_vehicles
        ).order_by('-entry_time')
        
        # Статистика
        active_sessions = parking_sessions.filter(exit_time__isnull=True)
        total_spent = parking_sessions.aggregate(
            total=Sum('total_cost')
        )['total'] or 0
        
        session_count = parking_sessions.count()
        
    except CarOwner.DoesNotExist:
        parking_sessions = []
        active_sessions = []
        total_spent = 0
        session_count = 0
    
    context = {
        'parking_sessions': parking_sessions,
        'active_sessions': active_sessions,
        'total_spent': total_spent,
        'session_count': session_count,
    }
    return render(request, 'users/parking_sessions.html', context)

@login_required
def payments_view(request):
    """Страница с платежами пользователя"""
    try:
        car_owner = CarOwner.objects.get(user=request.user)
        # Получаем все парковочные сессии пользователя
        user_vehicles = Vehicle.objects.filter(owner=car_owner)
        user_sessions = ParkingSession.objects.filter(vehicle__in=user_vehicles)
        # Получаем платежи для этих сессий
        payments = Payment.objects.filter(
            parking_session__in=user_sessions
        ).order_by('-payment_date')
        
        # Статистика
        total_paid = payments.aggregate(total=Sum('amount'))['total'] or 0
        successful_payments = payments.filter(is_successful=True)
        
        payment_count = payments.count()
        successful_count = successful_payments.count()
        
    except CarOwner.DoesNotExist:
        payments = []
        total_paid = 0
        successful_payments = []
        payment_count = 0
        successful_count = 0
    
    context = {
        'payments': payments,
        'total_paid': total_paid,
        'payment_count': payment_count,
        'successful_count': successful_count,
    }
    return render(request, 'users/payments.html', context)

def logout_view(request):
    """Представление для выхода из системы"""
    auth_logout(request)
    return redirect('home')

@login_required
def admin_car_owners_short_view(request):
    """Простая страница владельцев автомобилей"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    owners = CarOwner.objects.all().order_by('-id')[:50]
    
    context = {
        'owners': owners,
    }
    return render(request, 'admin/car_owners_simple.html', context)

@login_required
def admin_license_plates_short_view(request):
    """Простая страница распознанных номеров"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    plates = LicensePlateDetection.objects.all().order_by('-detection_time')[:50]
    
    # Простая статистика
    today = datetime.now().date()
    today_plates = LicensePlateDetection.objects.filter(detection_time__date=today)
    
    context = {
        'plates': plates,
        'today_count': today_plates.count(),
        'unique_today': today_plates.values('license_plate').distinct().count(),
    }
    return render(request, 'admin/license_plates_simple.html', context)

@login_required
def admin_failed_payments_short_view(request):
    """Простая страница неуспешных платежей"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    failed_payments = Payment.objects.filter(is_successful=False).order_by('-payment_date')[:50]
    
    # Простая статистика
    successful_count = Payment.objects.filter(is_successful=True).count()
    failed_count = Payment.objects.filter(is_successful=False).count()
    total_payments = successful_count + failed_count
    
    success_rate = 0
    if total_payments > 0:
        success_rate = round((successful_count / total_payments) * 100, 1)
    
    context = {
        'failed_payments': failed_payments,
        'failed_count': failed_count,
        'successful_count': successful_count,
        'success_rate': success_rate,
        'total_payments': total_payments,
    }
    return render(request, 'admin/failed_payments_simple.html', context)
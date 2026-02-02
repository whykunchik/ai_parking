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

from django.db.models import Sum, Count

from datetime import datetime, timedelta
# datetime - работа с датой/временем
# timedelta - разница во времени
from .forms import UserRegistrationForm
# Импортируем форму

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


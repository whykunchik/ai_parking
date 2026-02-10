from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse  # Добавьте JsonResponse
from .models import CarOwner, Vehicle, ParkingSession, Payment, Tariff, LicensePlateDetection, VideoUpload
from django.db.models import Sum
from datetime import datetime, timedelta
from .forms import UserRegistrationForm 
from django.core.files.storage import FileSystemStorage
import os
from django.conf import settings
from django.utils import timezone
import uuid

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
                
                # Перенаправляем всех пользователей на одну панель
                return redirect('dashboard')
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
    
    # Обработка загрузки видео (AJAX)
    if request.method == 'POST' and request.FILES.get('video'):
        video_file = request.FILES['video']
        
        # Проверка формата видео
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        file_ext = os.path.splitext(video_file.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f"Неподдерживаемый формат видео. Разрешены: {', '.join(allowed_extensions)}"
                })
            else:
                messages.error(request, f"Неподдерживаемый формат видео. Разрешены: {', '.join(allowed_extensions)}")
                return redirect('admin_dashboard')
        
        # Создание директории для видео
        video_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/admin_videos')
        os.makedirs(video_dir, exist_ok=True)
        
        # Генерация уникального имени файла
        filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(video_dir, filename)
        
        try:
            # Сохранение видео файла
            with open(file_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)
            
            # Создание записи в базе данных
            video = VideoUpload.objects.create(
                original_filename=video_file.name,
                saved_filename=filename,
                file_path=file_path,
                file_size=video_file.size,
                status='pending'
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"Видео успешно загружено. ID: {video.id}"
                })
            else:
                messages.success(request, f"Видео успешно загружено. ID: {video.id}")
                return redirect('admin_dashboard')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f"Ошибка загрузки: {str(e)}"
                })
            else:
                messages.error(request, f"Ошибка загрузки: {str(e)}")
                return redirect('admin_dashboard')
    
    # Статистика видео
    video_stats = {
        'total': VideoUpload.objects.count(),
        'pending': VideoUpload.objects.filter(status='pending').count(),
        'completed': VideoUpload.objects.filter(status='completed').count(),
        'failed': VideoUpload.objects.filter(status='failed').count(),
    }
    
    # Недавно распознанные номера
    recent_plates = LicensePlateDetection.objects.all().order_by('-detection_time')[:10]
    
    context = {
        'user': request.user,
        'today': today,
        'total_parking_sessions': ParkingSession.objects.count(),
        'active_sessions': ParkingSession.objects.filter(exit_time__isnull=True).count(),
        'total_revenue': Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'today_sessions': ParkingSession.objects.filter(
            entry_time__date=today
        ).count(),
        'video_stats': video_stats,
        'recent_plates': recent_plates,
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

@login_required
def admin_photo_upload_view(request):
    """Просмотр всех загруженных фотографий"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'pending':
        photos = PhotoUpload.objects.filter(status='pending')
    elif status_filter == 'completed':
        photos = PhotoUpload.objects.filter(status='completed')
    elif status_filter == 'failed':
        photos = PhotoUpload.objects.filter(status='failed')
    else:
        photos = PhotoUpload.objects.all()
    
    # Статистика
    stats = {
        'total': PhotoUpload.objects.count(),
        'pending': PhotoUpload.objects.filter(status='pending').count(),
        'completed': PhotoUpload.objects.filter(status='completed').count(),
        'failed': PhotoUpload.objects.filter(status='failed').count(),
    }
    
    context = {
        'user': request.user,
        'photos': photos,
        'stats': stats,
        'current_filter': status_filter,
    }
    
    return render(request, 'admin/photo_uploads.html', context)

def process_photo(photo_id):
    """Функция обработки фотографии и распознавания номера"""
    try:
        photo = PhotoUpload.objects.get(id=photo_id)
        photo.status = 'processing'
        photo.save()
        
        # Здесь будет ваша логика распознавания номера
        # Для примера, извлечем "номер" из имени файла или сгенерируем тестовый
        import re
        
        # Пример: ищем паттерны номера в имени файла
        filename = photo.original_filename
        plate_pattern = r'([A-ZА-Я]\d{3}[A-ZА-Я]{2}\d{2,3})|(\d{4}[A-ZА-Я]{2}\d{2})'
        matches = re.findall(plate_pattern, filename.upper())
        
        detected_plate = None
        if matches:
            for match in matches:
                for group in match:
                    if group:
                        detected_plate = group
                        break
        
        # Если не нашли в имени файла, генерируем тестовый номер
        if not detected_plate:
            import random
            letters = 'АВЕКМНОРСТУХ'
            numbers = '0123456789'
            detected_plate = f"{random.choice(letters)}{random.choice(numbers)}{random.choice(numbers)}{random.choice(numbers)}{random.choice(letters)}{random.choice(letters)}"
        
        # Сохраняем распознанный номер в LicensePlateDetection
        license_plate = LicensePlateDetection.objects.create(
            license_plate=detected_plate,
            image_path=photo.file_path,
            detection_time=timezone.now()
        )
        
        # Обновляем статус фото и сохраняем распознанный номер
        photo.status = 'completed'
        photo.detected_license_plate = detected_plate
        photo.save()
        
        # УДАЛЯЕМ оригинальный файл после успешной обработки
        if os.path.exists(photo.file_path):
            os.remove(photo.file_path)
        
        return True, detected_plate
        
    except Exception as e:
        photo = PhotoUpload.objects.get(id=photo_id)
        photo.status = 'failed'
        photo.error_message = str(e)
        photo.save()
        return False, str(e)

@login_required
def admin_process_photos_view(request):
    """Обработка фотографий"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    if request.method == 'POST':
        photo_id = request.POST.get('photo_id')
        if photo_id:
            success, result = process_photo(photo_id)
            if success:
                messages.success(request, f"Фото обработано успешно. Распознан номер: {result}")
            else:
                messages.error(request, f"Ошибка обработки: {result}")
            return redirect('admin_photo_uploads')
    
    # Статистика для страницы обработки
    pending_photos = PhotoUpload.objects.filter(status='pending')
    recent_processed = PhotoUpload.objects.filter(status='completed').order_by('-id')[:10]
    recent_failed = PhotoUpload.objects.filter(status='failed').order_by('-id')[:10]
    
    context = {
        'user': request.user,
        'total_pending': pending_photos.count(),
        'recent_processed': recent_processed,
        'recent_failed': recent_failed,
    }
    
    return render(request, 'admin/process_photos.html', context)

@login_required
def admin_video_upload_view(request):
    """Загрузка видео для анализа номеров"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    if request.method == 'POST' and request.FILES.get('video'):
        video_file = request.FILES['video']
        
        # Проверка формата видео
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        file_ext = os.path.splitext(video_file.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            messages.error(request, f"Неподдерживаемый формат видео. Разрешены: {', '.join(allowed_extensions)}")
            return render(request, 'admin/upload_video.html')
        
        # Создание директории для видео
        video_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/admin_videos')
        os.makedirs(video_dir, exist_ok=True)
        
        # Генерация уникального имени файла
        filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(video_dir, filename)
        
        # Сохранение видео файла
        with open(file_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        # Создание записи в базе данных
        video = VideoUpload.objects.create(
            original_filename=video_file.name,
            saved_filename=filename,
            file_path=file_path,
            file_size=video_file.size,
            status='pending'
        )
        
        messages.success(request, f"Видео успешно загружено. ID: {video.id}")
        return redirect('admin_video_uploads')
    
    return render(request, 'admin/upload_video.html')

@login_required
def admin_video_uploads_view(request):
    """Просмотр всех загруженных видео"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'pending':
        videos = VideoUpload.objects.filter(status='pending')
    elif status_filter == 'completed':
        videos = VideoUpload.objects.filter(status='completed')
    elif status_filter == 'failed':
        videos = VideoUpload.objects.filter(status='failed')
    else:
        videos = VideoUpload.objects.all()
    
    # Статистика
    stats = {
        'total': VideoUpload.objects.count(),
        'pending': VideoUpload.objects.filter(status='pending').count(),
        'completed': VideoUpload.objects.filter(status='completed').count(),
        'failed': VideoUpload.objects.filter(status='failed').count(),
    }
    
    # Получаем все распознанные номера из существующей папки с фото
    photo_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/admin_photos')
    detected_plates = []
    
    if os.path.exists(photo_dir):
        # Получаем все записи из LicensePlateDetection
        license_plates = LicensePlateDetection.objects.all().order_by('-detection_time')[:50]
        for plate in license_plates:
            detected_plates.append({
                'license_plate': plate.license_plate,
                'detection_time': plate.detection_time,
                'image_path': plate.image_path
            })
    
    context = {
        'user': request.user,
        'videos': videos,
        'stats': stats,
        'current_filter': status_filter,
        'detected_plates': detected_plates,
        'detected_count': len(detected_plates),
    }
    
    return render(request, 'admin/video_uploads.html', context)

@login_required
def extract_frames_from_video(request, video_id):
    """Извлечение кадров из видео (для демонстрации)"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    try:
        video = VideoUpload.objects.get(id=video_id)
        
        # Обновляем статус видео
        video.status = 'processing'
        video.save()
        
        # Пытаемся импортировать OpenCV (если установлен)
        try:
            import cv2
        except ImportError:
            video.status = 'failed'
            video.error_message = "OpenCV не установлен. Установите: pip install opencv-python"
            video.save()
            messages.error(request, "OpenCV не установлен. Установите: pip install opencv-python")
            return redirect('admin_video_uploads')
        
        # Создаем временный каталог для кадров
        frames_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/video_frames', str(video_id))
        os.makedirs(frames_dir, exist_ok=True)
        
        # Открываем видео
        cap = cv2.VideoCapture(video.file_path)
        frame_count = 0
        extracted_frames = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Сохраняем каждый 10-й кадр
            if frame_count % 10 == 0:
                frame_filename = f"frame_{frame_count:04d}.jpg"
                frame_path = os.path.join(frames_dir, frame_filename)
                cv2.imwrite(frame_path, frame)
                extracted_frames.append({
                    'filename': frame_filename,
                    'path': frame_path,
                    'url': f"/media/uploads/video_frames/{video_id}/{frame_filename}"
                })
            
            frame_count += 1
        
        cap.release()
        
        # Создаем демо-номера для распознавания (заглушка)
        for i, frame in enumerate(extracted_frames[:5]):  # Только первые 5 кадров
            import random
            letters = 'АВЕКМНОРСТУХ'
            numbers = '0123456789'
            plate_number = f"{random.choice(letters)}{random.choice(numbers)}{random.choice(numbers)}{random.choice(numbers)}{random.choice(letters)}{random.choice(letters)}"
            
            # Сохраняем в LicensePlateDetection
            LicensePlateDetection.objects.create(
                license_plate=plate_number,
                image_path=frame['path'],
                detection_time=timezone.now()
            )
        
        # Обновляем статус видео
        video.status = 'completed'
        video.save()
        
        messages.success(request, f"Извлечено {len(extracted_frames)} кадров из видео")
        
    except Exception as e:
        video.status = 'failed'
        video.error_message = str(e)
        video.save()
        messages.error(request, f"Ошибка обработки видео: {str(e)}")
    
    return redirect('admin_video_uploads')

def delete_video(request, video_id):
    """Удаление видео"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    try:
        video = VideoUpload.objects.get(id=video_id)
        
        # Удаляем файл
        if os.path.exists(video.file_path):
            os.remove(video.file_path)
        
        # Удаляем запись из БД
        video.delete()
        
        messages.success(request, "Видео успешно удалено")
    except Exception as e:
        messages.error(request, f"Ошибка удаления видео: {str(e)}")
    
    return redirect('admin_video_uploads')

@login_required
def admin_video_upload_view(request):
    """Загрузка видео для анализа номеров"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    if request.method == 'POST' and request.FILES.get('video'):
        video_file = request.FILES['video']
        
        # Проверка формата видео
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        file_ext = os.path.splitext(video_file.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            messages.error(request, f"Неподдерживаемый формат видео. Разрешены: {', '.join(allowed_extensions)}")
            return render(request, 'admin/upload_video.html')
        
        # Создание директории для видео
        video_dir = os.path.join(settings.MEDIA_ROOT, 'uploads/admin_videos')
        os.makedirs(video_dir, exist_ok=True)
        
        # Генерация уникального имени файла
        filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(video_dir, filename)
        
        # Сохранение видео файла
        with open(file_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        # Создание записи в базе данных
        video = VideoUpload.objects.create(
            original_filename=video_file.name,
            saved_filename=filename,
            file_path=file_path,
            file_size=video_file.size,
            status='pending'
        )
        
        messages.success(request, f"Видео успешно загружено. ID: {video.id}")
        return redirect('admin_video_uploads')
    
    return render(request, 'admin/upload_video.html')

@login_required
def admin_video_uploads_view(request):
    """Просмотр всех загруженных видео"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'pending':
        videos = VideoUpload.objects.filter(status='pending')
    elif status_filter == 'completed':
        videos = VideoUpload.objects.filter(status='completed')
    elif status_filter == 'failed':
        videos = VideoUpload.objects.filter(status='failed')
    else:
        videos = VideoUpload.objects.all()
    
    # Статистика
    stats = {
        'total': VideoUpload.objects.count(),
        'pending': VideoUpload.objects.filter(status='pending').count(),
        'completed': VideoUpload.objects.filter(status='completed').count(),
        'failed': VideoUpload.objects.filter(status='failed').count(),
    }
    
    # Получаем все распознанные номера
    license_plates = LicensePlateDetection.objects.all().order_by('-detection_time')[:50]
    
    context = {
        'user': request.user,
        'videos': videos,
        'stats': stats,
        'current_filter': status_filter,
        'detected_plates': license_plates,
        'detected_count': license_plates.count(),
    }
    
    return render(request, 'admin/video_uploads.html', context)

@login_required
def extract_frames_from_video(request, video_id):
    """Извлечение кадров из видео (упрощенная версия без OpenCV)"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    try:
        video = VideoUpload.objects.get(id=video_id)
        
        # Обновляем статус видео
        video.status = 'completed'
        video.save()
        
        # Создаем демо-номера для распознавания (заглушка)
        import random
        letters = 'АВЕКМНОРСТУХ'
        numbers = '0123456789'
        
        for i in range(5):  # Создаем 5 демо-записей
            plate_number = f"{random.choice(letters)}{random.choice(numbers)}{random.choice(numbers)}{random.choice(numbers)}{random.choice(letters)}{random.choice(letters)}"
            
            # Сохраняем в LicensePlateDetection
            LicensePlateDetection.objects.create(
                license_plate=plate_number,
                image_path=f"/media/uploads/video_frames/{video_id}/frame_{i:04d}.jpg",
                detection_time=timezone.now()
            )
        
        messages.success(request, f"Создано 5 демо-записей номеров для видео {video_id}")
        
    except Exception as e:
        video.status = 'failed'
        video.error_message = str(e)
        video.save()
        messages.error(request, f"Ошибка обработки видео: {str(e)}")
    
    return redirect('admin_video_uploads')

def delete_video(request, video_id):
    """Удаление видео"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещен")
        return redirect('dashboard')
    
    try:
        video = VideoUpload.objects.get(id=video_id)
        
        # Удаляем файл
        if os.path.exists(video.file_path):
            os.remove(video.file_path)
        
        # Удаляем запись из БД
        video.delete()
        
        messages.success(request, "Видео успешно удалено")
    except Exception as e:
        messages.error(request, f"Ошибка удаления видео: {str(e)}")
    
    return redirect('admin_video_uploads')
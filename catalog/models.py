from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User  # Стандартная модель пользователя Django
from django.core.validators import MinLengthValidator  # Валидатор минимальной длины
from typing import Optional, Any
from django.utils import timezone

#Владелец автомобиля
class CarOwner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # OneToOneField - один к одному с User (у одного пользователя один профиль владельца)
    # CASCADE - при удалении пользователя удаляется и профиль
    
    phone = models.CharField(max_length=11)  # Телефон, максимум 11 символов
    
    class Meta:
        verbose_name = 'Владелец автомобиля'  # Имя владельца
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"  # Строковое представление
    
# Модель транспортного средства
class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('car', 'Легковой автомобиль'),
        ('truck', 'Грузовик'),
        ('motorcycle', 'Мотоцикл'),
        ('bus', 'Автобус'),
    ]
    
    owner = models.ForeignKey(CarOwner, on_delete=models.CASCADE)
    state_number = models.CharField(max_length=9, unique=True)
    brand = models.CharField(max_length=100, verbose_name='Марка')
    model = models.CharField(max_length=100, verbose_name='Модель')
    color = models.CharField(max_length=50, verbose_name='Цвет')
    year = models.PositiveIntegerField(verbose_name='Год выпуска')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default='car', verbose_name='Тип ТС')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Транспортное средство'
    
    def __str__(self):
        return f"{self.state_number}"
    
# Модель парковочной сессии
class ParkingSession(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    # Связь с Vehicle

    entry_time = models.DateTimeField()  # Время въезда
    exit_time = models.DateTimeField(null=True, blank=True) # null=True - может быть NULL в БД  blank=True - может быть пустым в формах
    total_time_minutes = models.PositiveIntegerField(default=0)  # Общее время в минутах
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)  # Стоимость
    # DecimalField для точных денежных расчетов
    # max_digits=10 - максимум 10 цифр
    # decimal_places=2 - 2 знака после запятой
    is_paid = models.BooleanField(default=False)  # Оплачена ли сессия
    
    class Meta:
        verbose_name = 'Парковочная сессия'
        ordering = ['-entry_time']  # Сортировка по убыванию времени въезда
    
    def __str__(self):
        return f"{self.vehicle.state_number} - {self.entry_time}"

# Модель платежа
class Payment(models.Model):

    PAYMENT_METHODS = [  # Константы для выбора метода оплаты
        ('cash', 'Наличные'),  # ('значение в БД')
        ('card', 'Банковская карта'),
        ('online', 'Онлайн-оплата'),
    ]

    parking_session = models.ForeignKey(ParkingSession, on_delete=models.CASCADE)
    # Связь с ParkingSession

    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Сумма платежа
    payment_date = models.DateTimeField(auto_now_add=True)  # Дата платежа (автоматически)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)  # Метод оплаты
    # choices - ограничивает выбор значениями из PAYMENT_METHODS
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)  # ID транзакции
    # unique=True - уникальный идентификатор
    # blank=True, null=True - может быть пустым
    is_successful = models.BooleanField(default=True)  # Успешен ли платеж
    
    class Meta:
        verbose_name = 'Платеж'
        ordering = ['-payment_date']  # Сортировка по убыванию даты
    
    def __str__(self):
        return f"Платеж {self.transaction_id} - {self.amount} руб."

# Модель тарифа
class Tariff(models.Model):
    name = models.CharField(max_length=100)  # Название тарифа
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)  # Цена за час
    is_active = models.BooleanField(default=True)  # Активен ли тариф
    
    class Meta:
        verbose_name = 'Тариф'
    
    def __str__(self):
        return f"{self.name} - {self.price_per_hour} руб./час"
    
# Модель для хранения результатов распознавания номеров
class LicensePlateDetection(models.Model):
    license_plate = models.CharField(max_length=15)  # Распознанный номер
    image_path = models.CharField(max_length=255, blank=True, null=True)  # Путь к изображению
    detection_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Распознанный номер'
        verbose_name_plural = 'Распознанные номера'
        ordering = ['-detection_time']  # Свежие записи сверху
    
    def __str__(self):
        return f"{self.license_plate}"
    
class VehicleRequest(models.Model):
    REQUEST_STATUS = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]
    
    owner = models.ForeignKey(CarOwner, on_delete=models.CASCADE, verbose_name='Владелец')
    state_number = models.CharField(max_length=9, verbose_name='Гос. номер')
    brand = models.CharField(max_length=100, verbose_name='Марка')
    model = models.CharField(max_length=100, verbose_name='Модель')
    color = models.CharField(max_length=50, verbose_name='Цвет')
    year = models.PositiveIntegerField(verbose_name='Год выпуска')
    vehicle_type = models.CharField(
        max_length=20, 
        choices=Vehicle.VEHICLE_TYPES,  # Используем тот же выбор что и в Vehicle
        default='car', 
        verbose_name='Тип ТС'
    )
    
    status = models.CharField(
        max_length=10, 
        choices=REQUEST_STATUS, 
        default='pending', 
        verbose_name='Статус'
    )
    request_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата запроса')
    processed_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата обработки')
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='Обработал',
        related_name='processed_vehicle_requests'
    )
    rejection_reason = models.TextField(blank=True, null=True, verbose_name='Причина отказа')
    
    class Meta:
        verbose_name = 'Запрос на добавление автомобиля'
        verbose_name_plural = 'Запросы на добавление автомобилей'
        ordering = ['-request_date']
    
    def __str__(self):
        return f"Запрос {self.id}: {self.state_number} ({self.get_status_display()})"
    
    def approve(self, user):
        """Одобрить запрос и создать автомобиль"""
        from django.utils import timezone
        
        # Создаем автомобиль
        vehicle = Vehicle.objects.create(
            owner=self.owner,
            state_number=self.state_number,
            brand=self.brand,
            model=self.model,
            color=self.color,
            year=self.year,
            vehicle_type=self.vehicle_type,
            is_active=True
        )
        
        # Обновляем статус запроса
        self.status = 'approved'
        self.processed_date = timezone.now()
        self.processed_by = user
        self.save()
        
        return vehicle
    
    def reject(self, user, reason):
        """Отклонить запрос"""
        from django.utils import timezone
        
        self.status = 'rejected'
        self.processed_date = timezone.now()
        self.processed_by = user
        self.rejection_reason = reason
        self.save()
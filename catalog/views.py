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

from django.shortcuts import render
from .models import Car, Time

def index(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    num_car=Car.objects.all().count()

    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    return render(
        request,
        'index.html',
        context={'num_books':num_car},
    )
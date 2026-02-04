"""
URL configuration for ai_parking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.urls import include
from django.views.generic import TemplateView, RedirectView
from catalog.views import (
    login_view, user_dashboard_view, admin_dashboard_view, 
    register_view, my_vehicles_view, parking_sessions_view, 
    payments_view, logout_view  
)
urlpatterns = [
    path('catalog/', RedirectView.as_view(url='/', permanent=True)),
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', user_dashboard_view, name='dashboard'),
    path('admin-dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('my-vehicles/', my_vehicles_view, name='my_vehicles'),
    path('parking-sessions/', parking_sessions_view, name='parking_sessions'),
    path('payments/', payments_view, name='payments'),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]
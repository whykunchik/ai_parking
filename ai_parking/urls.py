from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView
from django.conf import settings
from django.conf.urls.static import static
from catalog.views import (
    login_view, user_dashboard_view, admin_dashboard_view, 
    register_view, parking_sessions_view, 
    payments_view, logout_view, admin_car_owners_short_view,
    admin_license_plates_short_view, admin_failed_payments_short_view,
    admin_video_uploads_view, extract_frames_from_video, delete_video,
)

urlpatterns = [  
    # Административные страницы  
    path('admin/car-owners-simple/', admin_car_owners_short_view, name='admin_car_owners_simple'),    
    path('admin/license-plates-simple/', admin_license_plates_short_view, name='admin_license_plates_simple'),
    path('admin/failed-payments-simple/', admin_failed_payments_short_view, name='admin_failed_payments_simple'),
    path('admin/video-uploads/', admin_video_uploads_view, name='admin_video_uploads'),
    path('admin/extract-frames/<int:video_id>/', extract_frames_from_video, name='extract_frames'),
    path('admin/delete-video/<int:video_id>/', delete_video, name='delete_video'),

    # Основные страницы
    path('catalog/', RedirectView.as_view(url='/', permanent=True)),
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Пользовательские страницы    
    path('dashboard/', user_dashboard_view, name='dashboard'),
    path('parking-sessions/', parking_sessions_view, name='parking_sessions'),
    path('payments/', payments_view, name='payments'),
    
    # Административные страницы    
    path('admin-dashboard/', admin_dashboard_view, name='admin_dashboard'),
    
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
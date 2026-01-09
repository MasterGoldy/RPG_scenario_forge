"""
URL configuration for rpg_scenario_forge project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Админ-панель
    path('admin/', admin.site.urls),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html',
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='home'
    ), name='logout'),

    # Основное приложение
    path('', include('core.urls')),
]

# Обслуживание статических файлов в разработке
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Кастомный заголовок админки
admin.site.site_header = 'RPG Scenario Forge Администрация'
admin.site.site_title = 'RPG Scenario Forge'
admin.site.index_title = 'Управление платформой'
"""
URL configuration for rpg_scenario_forge project.
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core import views as core_views

urlpatterns = [

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', core_views.register, name='register'),

    # Core app
    path('', core_views.home, name='home'),
    path('scenarios/', core_views.scenario_list, name='scenario_list'),
    path('scenarios/create/', core_views.scenario_create, name='scenario_create'),
    path('scenarios/<int:pk>/', core_views.scenario_detail, name='scenario_detail'),
    path('scenarios/<int:pk>/edit/', core_views.scenario_edit, name='scenario_edit'),
    path('scenarios/<int:pk>/delete/', core_views.scenario_delete, name='scenario_delete'),
    path('scenarios/<int:pk>/analyze/', core_views.scenario_analyze, name='scenario_analyze'),
    path('favorite/<int:pk>/', core_views.toggle_favorite, name='toggle_favorite'),

    # API endpoints
    path('api/scenarios/', core_views.api_scenario_list, name='api_scenario_list'),
    path('api/scenarios/<int:pk>/', core_views.api_scenario_detail, name='api_scenario_detail'),

    # Publication
    path('scenarios/<int:pk>/publish/', core_views.scenario_publish, name='scenario_publish'),
    path('scenarios/<int:pk>/unpublish/', core_views.scenario_unpublish, name='scenario_unpublish'),
    path('scenarios/<int:scenario_id>/analyze/', core_views.scenario_analyze, name='scenario_analyze'),

    # Авторизация
    path('register/', core_views.register_view, name='register'),
    path('login/', core_views.login_view, name='login'),
    path('logout/', core_views.logout_view, name='logout'),
    path('profile/', core_views.profile_view, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
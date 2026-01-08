from django.contrib import admin
from django.utils.html import format_html
from .models import (
    GameSystem, Scenario, ScenarioElement,
    AnalysisResult, UserProfile, Favorite
)


@admin.register(GameSystem)
class GameSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'game_system',
        'difficulty', 'status', 'is_public',
        'created_at', 'views', 'favorites'
    )
    list_filter = ('status', 'is_public', 'game_system', 'difficulty')
    search_fields = ('title', 'description', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'views', 'favorites')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'content', 'author', 'game_system')
        }),
        ('Настройки сложности', {
            'fields': ('difficulty', 'estimated_play_time', 'recommended_players', 'recommended_level')
        }),
        ('Аналитика', {
            'fields': ('combat_balance_score', 'puzzle_complexity_score', 'narrative_coherence')
        }),
        ('Метаданные', {
            'fields': ('status', 'is_public', 'tags')
        }),
        ('Статистика', {
            'fields': ('views', 'favorites', 'created_at', 'updated_at', 'published_at')
        }),
    )

    def view_on_site(self, obj):
        return obj.get_absolute_url()


@admin.register(ScenarioElement)
class ScenarioElementAdmin(admin.ModelAdmin):
    list_display = ('name', 'element_type', 'scenario', 'challenge_rating')
    list_filter = ('element_type',)
    search_fields = ('name', 'description', 'scenario__title')
    readonly_fields = ('created_at',)


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('scenario', 'analysis_type', 'confidence_score', 'created_at')
    list_filter = ('analysis_type',)
    search_fields = ('scenario__title', 'recommendations')
    readonly_fields = ('created_at', 'execution_time')

    def has_add_permission(self, request):
        return False  # Запрещаем создавать через админку


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_level', 'scenarios_created', 'scenarios_published')
    search_fields = ('user__username', 'user__email', 'bio')
    list_filter = ('experience_level',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario', 'created_at')
    search_fields = ('user__username', 'scenario__title')
    list_filter = ('created_at',)
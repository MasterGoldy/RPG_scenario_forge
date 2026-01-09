"""
Views для RPG Scenario Forge.
"""
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET, require_POST
import plotly.graph_objects as go
import plotly.offline as opy
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Scenario, ScenarioElement, AnalysisResult, GameSystem, UserProfile, Favorite
from .forms import UserRegisterForm, ScenarioForm, SearchForm, AnalysisSettingsForm, UserProfileForm, RegisterForm, LoginForm
from .utils import ScenarioAnalyzer, CombatBalanceAnalyzer, TextAnalyzer


def home(request):
    """Главная страница"""
    # Получаем статистику
    stats = {
        'total_scenarios': Scenario.objects.filter(status='published', is_public=True).count(),
        'total_authors': Scenario.objects.filter(status='published')
        .values('author').distinct().count(),
        'avg_combat_score': Scenario.objects.filter(status='published')
                            .aggregate(avg=Avg('combat_balance_score'))['avg'] or 0,
        'total_elements': ScenarioElement.objects.count(),
    }

    # Получаем последние сценарии
    recent_scenarios = Scenario.objects.filter(
        status='published',
        is_public=True
    ).select_related('author', 'game_system').order_by('-created_at')[:4]

    # Получаем популярные игровые системы
    popular_systems = GameSystem.objects.filter(
        is_active=True,
        scenario__status='published'
    ).annotate(
        scenario_count=Count('scenario')
    ).order_by('-scenario_count')[:5]

    context = {
        'stats': stats,
        'recent_scenarios': recent_scenarios,
        'popular_systems': popular_systems,
        'title': 'Главная',
    }

    return render(request, 'core/home.html', context)


def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Автоматически логиним пользователя
            login(request, user)

            # Создаем профиль пользователя
            from .models import UserProfile
            UserProfile.objects.create(user=user)

            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('index')
    else:
        form = RegisterForm()

    return render(request, 'core/auth/register.html', {
        'form': form,
        'title': 'Регистрация'
    })


def login_view(request):
    """Вход в систему"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')

                # Перенаправляем на следующую страницу или на главную
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'core/auth/login.html', {
        'form': form,
        'title': 'Вход в систему'
    })


@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы')
    return redirect('index')


def index(request):
    """Главная страница"""
    # Показываем последние публичные сценарии
    public_scenarios = Scenario.objects.filter(
        status='published',
        is_public=True
    ).select_related('author', 'game_system').order_by('-created_at')[:6]

    # Статистика для главной страницы
    stats = {
        'total_scenarios': Scenario.objects.filter(status='published', is_public=True).count(),
        'total_users': User.objects.count(),
        'total_systems': GameSystem.objects.count(),
    }

    context = {
        'public_scenarios': public_scenarios,
        'stats': stats,
        'featured_systems': GameSystem.objects.filter(is_active=True)[:5],
    }

    # Если пользователь авторизован, показываем его сценарии
    if request.user.is_authenticated:
        context['user_scenarios'] = Scenario.objects.filter(
            author=request.user
        ).order_by('-created_at')[:3]

    return render(request, 'core/index.html', context)


@login_required
def profile_view(request):
    """Профиль пользователя"""
    user = request.user

    # Получаем или создаем профиль
    from .models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Статистика пользователя
    user_stats = {
        'scenarios_created': Scenario.objects.filter(author=user).count(),
        'scenarios_published': Scenario.objects.filter(author=user, status='published').count(),
        'total_views': Scenario.objects.filter(author=user).aggregate(
            total= sum('views')
        )['total'] or 0,
        'favorites': Scenario.objects.filter(author=user).aggregate(
            total= sum('favorites')
        )['total'] or 0,
    }

    # Последние сценарии пользователя
    recent_scenarios = Scenario.objects.filter(author=user).order_by('-created_at')[:5]

    if request.method == 'POST':
        # Обновление профиля
        profile.bio = request.POST.get('bio', '')
        profile.experience_level = request.POST.get('experience_level', 'intermediate')
        profile.save()

        # Обновление email пользователя
        new_email = request.POST.get('email', '')
        if new_email and new_email != user.email:
            user.email = new_email
            user.save()

        messages.success(request, 'Профиль обновлен')
        return redirect('profile')

    return render(request, 'core/auth/profile.html', {
        'profile': profile,
        'user_stats': user_stats,
        'recent_scenarios': recent_scenarios,
        'title': 'Мой профиль'
    })

def scenario_list(request):
    """Список всех сценариев"""
    # Получаем ВСЕ сценарии для администраторов и авторов
    scenarios = Scenario.objects.all()

    # Для неавторизованных пользователей показываем только опубликованные и публичные
    if not request.user.is_authenticated:
        scenarios = scenarios.filter(status='published', is_public=True)
    else:
        # Для авторизованных показываем их черновики + все опубликованные
        scenarios = scenarios.filter(
            Q(status='published', is_public=True) |
            Q(author=request.user)  # Показываем свои сценарии в любом статусе
        )

    # Применяем фильтры поиска
    search_form = SearchForm(request.GET or None)

    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        game_system = search_form.cleaned_data.get('game_system')
        difficulty = search_form.cleaned_data.get('difficulty')
        min_play_time = search_form.cleaned_data.get('min_play_time')
        max_play_time = search_form.cleaned_data.get('max_play_time')
        sort_by = search_form.cleaned_data.get('sort_by') or '-created_at'

        if query:
            scenarios = scenarios.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(content__icontains=query)
            )

        if game_system:
            scenarios = scenarios.filter(game_system=game_system)

        if difficulty:
            scenarios = scenarios.filter(difficulty=difficulty)

        if min_play_time:
            scenarios = scenarios.filter(estimated_play_time__gte=min_play_time)

        if max_play_time:
            scenarios = scenarios.filter(estimated_play_time__lte=max_play_time)

        scenarios = scenarios.order_by(sort_by)
    else:
        scenarios = scenarios.order_by('-created_at')

    # Пагинация
    paginator = Paginator(scenarios, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'scenarios': page_obj.object_list,  # Добавляем для прямого доступа
        'search_form': search_form,
        'game_systems': GameSystem.objects.filter(is_active=True),
        'title': 'Все сценарии',
        'total_count': paginator.count,
        'is_authenticated': request.user.is_authenticated,
    }

    return render(request, 'core/scenario_list.html', context)

@login_required
def scenario_delete(request, scenario_id):
    """Удаление сценария"""
    scenario = get_object_or_404(Scenario, id=scenario_id)

    # Проверка прав (только автор может удалять)
    if scenario.author != request.user and not request.user.is_staff:
        messages.error(request, "Вы не можете удалить этот сценарий")
        return redirect('scenario_detail', scenario_id=scenario.id)

    if request.method == 'POST':
        scenario.delete()
        messages.success(request, f'Сценарий "{scenario.title}" успешно удален')
        return redirect('scenario_list')  # или на свою страницу со списком

    # GET запрос - показать подтверждение
    return render(request, 'core/scenario_confirm_delete.html', {
        'scenario': scenario
    })

@login_required
def scenario_publish(request, pk):
    """Публикация сценария"""
    scenario = get_object_or_404(Scenario, pk=pk)

    if scenario.author != request.user:
        messages.error(request, 'Вы можете публиковать только свои сценарии.')
        return redirect('scenario_detail', pk=pk)

    scenario.status = 'published'
    scenario.is_public = request.POST.get('is_public') == 'on'
    scenario.published_at = timezone.now()
    scenario.save()

    # Обновляем статистику пользователя
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile.scenarios_published += 1
    profile.save()

    messages.success(request, 'Сценарий успешно опубликован!')
    return redirect('scenario_detail', pk=pk)

@login_required
def scenario_unpublish(request, pk):
    """Возврат сценария в черновики"""
    scenario = get_object_or_404(Scenario, pk=pk)

    if scenario.author != request.user:
        messages.error(request, 'Вы можете изменять только свои сценарии.')
        return redirect('scenario_detail', pk=pk)

    scenario.status = 'draft'
    scenario.save()

    messages.info(request, 'Сценарий перемещен в черновики.')
    return redirect('scenario_detail', pk=pk)

@login_required
def scenario_create(request):
    """Создание нового сценария"""
    if request.method == 'POST':
        form = ScenarioForm(request.POST)
        if form.is_valid():
            # Сохраняем сценарий, но не коммитим в БД пока
            scenario = form.save(commit=False)

            # Устанавливаем автора
            scenario.author = request.user

            # Устанавливаем статус по умолчанию
            scenario.status = 'draft'

            # Сохраняем в БД
            scenario.save()

            # Сохраняем ManyToMany связи если есть
            form.save_m2m()

            # Обновляем статистику пользователя
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.scenarios_created += 1
            profile.save()

            messages.success(request, 'Сценарий успешно создан!')
            return redirect('scenario_detail', pk=scenario.pk)
        else:
            # Если форма невалидна, покажем ошибки
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
            print("Ошибки формы:", form.errors)  # Для отладки
    else:
        form = ScenarioForm()

    context = {
        'form': form,
        'title': 'Создание сценария',
    }

    return render(request, 'core/scenario_form.html', context)


@login_required
def scenario_edit(request, pk):
    """Редактирование существующего сценария"""
    scenario = get_object_or_404(Scenario, pk=pk)

    # Проверяем права доступа
    if scenario.author != request.user:
        messages.error(request, 'Вы можете редактировать только свои сценарии.')
        return redirect('scenario_detail', pk=pk)

    if request.method == 'POST':
        form = ScenarioForm(request.POST, instance=scenario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сценарий успешно обновлен!')
            return redirect('scenario_detail', pk=pk)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки.')
    else:
        form = ScenarioForm(instance=scenario)

    context = {
        'form': form,
        'scenario': scenario,
        'title': f'Редактирование: {scenario.title}',
    }

    return render(request, 'core/scenario_form.html', context)


@login_required
def toggle_favorite(request, pk):
    """Добавление/удаление сценария из избранного"""
    scenario = get_object_or_404(Scenario, pk=pk)

    # Проверяем, уже ли в избранном
    favorite_exists = Favorite.objects.filter(
        user=request.user,
        scenario=scenario
    ).exists()

    if favorite_exists:
        # Удаляем из избранного
        Favorite.objects.filter(user=request.user, scenario=scenario).delete()
        scenario.favorites = max(0, scenario.favorites - 1)
        messages.success(request, 'Убрано из избранного')
    else:
        # Добавляем в избранное
        Favorite.objects.create(user=request.user, scenario=scenario)
        scenario.favorites += 1
        messages.success(request, 'Добавлено в избранное')

    scenario.save(update_fields=['favorites'])

    # Перенаправляем обратно на страницу сценария
    return redirect('scenario_detail', pk=pk)

def scenario_detail(request, pk):
    """Детальная страница сценария"""
    scenario = get_object_or_404(
        Scenario.objects.select_related('author', 'game_system'),
        pk=pk
    )

    # Проверяем доступ
    if scenario.status != 'published' and scenario.author != request.user:
        messages.error(request, 'Этот сценарий не опубликован.')
        return redirect('scenario_list')

    if not scenario.is_public and scenario.author != request.user:
        messages.error(request, 'У вас нет доступа к этому сценарию.')
        return redirect('scenario_list')

    # Увеличиваем счетчик просмотров
    if request.user != scenario.author:
        scenario.views += 1
        scenario.save(update_fields=['views'])

    # Получаем элементы сценария
    elements = scenario.elements.all()

    # Получаем результаты анализа
    analyses = scenario.analyses.all().order_by('-created_at')

    # Проверяем, в избранном ли
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(
            user=request.user, scenario=scenario
        ).exists()

    # Генерируем графики для аналитики
    charts = generate_analysis_charts(scenario, elements)

    context = {
        'scenario': scenario,
        'elements': elements,
        'analyses': analyses,
        'is_favorite': is_favorite,
        'can_edit': request.user == scenario.author,
        'charts': charts,
        'title': scenario.title,
    }

    return render(request, 'core/scenario_detail.html', context)


@login_required
def scenario_edit(request, pk):
    """Редактирование сценария"""
    scenario = get_object_or_404(Scenario, pk=pk)

    if scenario.author != request.user:
        messages.error(request, 'Вы можете редактировать только свои сценарии.')
        return redirect('scenario_detail', pk=pk)

    if request.method == 'POST':
        form = ScenarioForm(request.POST, instance=scenario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сценарий успешно обновлен!')
            return redirect('scenario_detail', pk=pk)
    else:
        form = ScenarioForm(instance=scenario)

    context = {
        'form': form,
        'scenario': scenario,
        'title': f'Редактирование: {scenario.title}',
        'game_systems': GameSystem.objects.filter(is_active=True),
    }

    return render(request, 'core/scenario_form.html', context)


@login_required
def scenario_delete(request, pk):
    """Удаление сценария"""
    scenario = get_object_or_404(Scenario, pk=pk)

    if scenario.author != request.user:
        messages.error(request, 'Вы можете удалять только свои сценарии.')
        return redirect('scenario_detail', pk=pk)

    if request.method == 'POST':
        scenario.delete()
        messages.success(request, 'Сценарий успешно удален.')
        return redirect('scenario_list')

    context = {
        'scenario': scenario,
        'title': 'Удаление сценария',
    }

    return render(request, 'core/scenario_confirm_delete.html', context)


@login_required
def scenario_analyze(request, pk):
    """Анализ сценария"""
    scenario = get_object_or_404(Scenario, pk=pk)

    if scenario.author != request.user:
        messages.error(request, 'Вы можете анализировать только свои сценарии.')
        return redirect('scenario_detail', pk=pk)

    if request.method == 'POST':
        form = AnalysisSettingsForm(request.POST)
        if form.is_valid():
            # Запускаем анализ
            analyzer = ScenarioAnalyzer()
            analysis_result = analyzer.full_analysis(
                scenario.content,
                party_level=form.cleaned_data.get('party_level', 3),
                party_size=form.cleaned_data.get('party_size', 4)
            )

            # Сохраняем результаты
            AnalysisResult.objects.create(
                scenario=scenario,
                analysis_type='full_analysis',
                results=analysis_result,
                recommendations=analysis_result.get('recommendations', []),
                confidence_score=analysis_result.get('overall_score', 0.5),
                execution_time=analysis_result.get('execution_time', 0)
            )

            # Обновляем оценки в сценарии
            scenario.combat_balance_score = analysis_result['combat_analysis'].get('balance_score', 0.5)
            scenario.puzzle_complexity_score = analysis_result['puzzle_analysis'].get('complexity_score', 0.5)
            scenario.narrative_coherence = analysis_result['narrative_analysis'].get('narrative_score', 0.5)
            scenario.save()

            messages.success(request, 'Анализ успешно выполнен!')
            return redirect('scenario_detail', pk=pk)
    else:
        form = AnalysisSettingsForm()

    context = {
        'scenario': scenario,
        'form': form,
        'title': f'Анализ сценария: {scenario.title}',
    }

    return render(request, 'core/scenario_analyze.html', context)


@login_required
def toggle_favorite(request, pk):
    """Добавление/удаление из избранного"""
    scenario = get_object_or_404(Scenario, pk=pk)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        scenario=scenario
    )

    if not created:
        favorite.delete()
        scenario.favorites -= 1
        messages.success(request, 'Убрано из избранного')
    else:
        scenario.favorites += 1
        messages.success(request, 'Добавлено в избранное')

    scenario.save(update_fields=['favorites'])

    return redirect('scenario_detail', pk=pk)


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Создаем профиль
            UserProfile.objects.create(user=user)

            # Авторизуем пользователя
            login(request, user)
            messages.success(request, 'Регистрация успешна! Добро пожаловать!')
            return redirect('home')
    else:
        form = UserRegisterForm()

    context = {
        'form': form,
        'title': 'Регистрация',
    }

    return render(request, 'core/register.html', context)


@login_required
def user_profile(request):
    """Профиль пользователя"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)

    # Получаем сценарии пользователя
    user_scenarios = Scenario.objects.filter(author=request.user).order_by('-created_at')

    # Получаем избранное
    favorites = Favorite.objects.filter(user=request.user).select_related('scenario')

    context = {
        'profile': profile,
        'form': form,
        'user_scenarios': user_scenarios,
        'favorites': favorites,
        'title': 'Мой профиль',
    }

    return render(request, 'core/user_profile.html', context)


@require_GET
def api_scenario_list(request):
    """API для получения списка сценариев"""
    scenarios = Scenario.objects.filter(status='published', is_public=True)

    # Фильтрация
    game_system = request.GET.get('game_system')
    difficulty = request.GET.get('difficulty')

    if game_system:
        scenarios = scenarios.filter(game_system__slug=game_system)

    if difficulty:
        scenarios = scenarios.filter(difficulty=difficulty)

    # Лимит
    limit = min(int(request.GET.get('limit', 20)), 100)
    scenarios = scenarios[:limit]

    data = []
    for scenario in scenarios:
        data.append({
            'id': scenario.id,
            'title': scenario.title,
            'description': scenario.description[:200] + '...' if len(
                scenario.description) > 200 else scenario.description,
            'author': scenario.author.username,
            'game_system': scenario.game_system.name,
            'difficulty': scenario.get_difficulty_display(),
            'estimated_play_time': scenario.estimated_play_time,
            'recommended_players': scenario.recommended_players,
            'views': scenario.views,
            'favorites': scenario.favorites,
            'created_at': scenario.created_at.isoformat(),
            'url': f'/scenarios/{scenario.id}/',
        })

    return JsonResponse({'scenarios': data, 'count': len(data)})


@require_GET
def api_scenario_detail(request, pk):
    """API для получения деталей сценария"""
    try:
        scenario = Scenario.objects.get(pk=pk, is_public=True, status='published')
    except Scenario.DoesNotExist:
        return JsonResponse({'error': 'Scenario not found or not public'}, status=404)

    data = {
        'id': scenario.id,
        'title': scenario.title,
        'description': scenario.description,
        'content_preview': scenario.content[:500] + '...' if len(scenario.content) > 500 else scenario.content,
        'author': scenario.author.username,
        'game_system': scenario.game_system.name,
        'difficulty': scenario.get_difficulty_display(),
        'estimated_play_time': scenario.estimated_play_time,
        'recommended_players': scenario.recommended_players,
        'recommended_level': scenario.recommended_level,
        'combat_balance_score': scenario.combat_balance_score,
        'puzzle_complexity_score': scenario.puzzle_complexity_score,
        'narrative_coherence': scenario.narrative_coherence,
        'word_count': scenario.word_count,
        'views': scenario.views,
        'favorites': scenario.favorites,
        'created_at': scenario.created_at.isoformat(),
        'updated_at': scenario.updated_at.isoformat(),
    }

    return JsonResponse(data)


def quick_analyze(request):
    """Быстрый анализ текста без сохранения"""
    if request.method == 'POST':
        text = request.POST.get('text', '')

        if not text or len(text) < 50:
            messages.error(request, 'Введите текст для анализа (минимум 50 символов)')
            return render(request, 'core/quick_analyze.html')

        analyzer = ScenarioAnalyzer()
        analysis = analyzer.full_analysis(text)

        # Генерируем графики
        charts = generate_quick_analysis_charts(analysis)

        context = {
            'analysis': analysis,
            'text': text,
            'charts': charts,
            'title': 'Быстрый анализ текста',
        }

        return render(request, 'core/quick_analyze_result.html', context)

    return render(request, 'core/quick_analyze.html', {'title': 'Быстрый анализ'})


# Вспомогательные функции
def generate_analysis_charts(scenario, elements):
    """Генерация графиков для анализа сценария"""
    charts = []

    # 1. График распределения элементов
    if elements:
        element_counts = {}
        for element in elements:
            element_type = element.get_element_type_display()
            element_counts[element_type] = element_counts.get(element_type, 0) + 1

        if element_counts:
            fig = go.Figure(data=[
                go.Pie(
                    labels=list(element_counts.keys()),
                    values=list(element_counts.values()),
                    hole=.3
                )
            ])
            fig.update_layout(title_text='Распределение элементов сценария')
            charts.append(opy.plot(fig, output_type='div', include_plotlyjs=False))

    # 2. График оценок
    scores = [
        ('Баланс боя', scenario.combat_balance_score),
        ('Сложность загадок', scenario.puzzle_complexity_score),
        ('Связность', scenario.narrative_coherence),
    ]

    if any(score[1] > 0 for score in scores):
        fig = go.Figure(data=[
            go.Bar(
                x=[s[0] for s in scores],
                y=[s[1] for s in scores],
                text=[f'{s[1]:.2f}' for s in scores],
                textposition='auto',
            )
        ])
        fig.update_layout(
            title_text='Оценки сценария',
            yaxis=dict(range=[0, 1])
        )
        charts.append(opy.plot(fig, output_type='div', include_plotlyjs=False))

    return charts


def generate_quick_analysis_charts(analysis):
    """Генерация графиков для быстрого анализа"""
    charts = []

    # График общего балла
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=analysis.get('overall_score', 0) * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Общий балл"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "green"}
            ],
        }
    ))
    charts.append(opy.plot(fig, output_type='div', include_plotlyjs=False))

    return charts

def get_game_systems(request):
    """Добавляет игровые системы в контекст"""
    return {
        'game_systems': GameSystem.objects.filter(is_active=True),
    }
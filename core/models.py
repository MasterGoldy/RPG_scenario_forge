"""
Модели данных для RPG Scenario Forge.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class GameSystem(models.Model):
    """Игровые системы (D&D 5e, Pathfinder и т.д.)"""
    name = models.CharField('Название системы', max_length=100)
    slug = models.SlugField('Слаг', unique=True)
    description = models.TextField('Описание', blank=True)
    srd_url = models.URLField('Ссылка на SRD', blank=True)
    is_active = models.BooleanField('Активна', default=True)

    @classmethod
    def create_default_systems(cls):
        """Создает стандартные игровые системы при первом запуске."""
        systems_data = [
            # D&D серия
            {'name': 'Dungeons & Dragons 5e', 'slug': 'dnd5e',
             'description': 'Самая популярная НРИ. Упрощенные правила, баланс между тактикой и ролеплеем.',
             'srd_url': 'https://www.dnd5esrd.com/'},
            {'name': 'Dungeons & Dragons 3.5', 'slug': 'dnd35',
             'description': 'Классика с детализированными правилами и огромным количеством дополнений.',
             'srd_url': 'https://www.d20srd.org/'},
            {'name': 'Dungeons & Dragons 4e', 'slug': 'dnd4e',
             'description': 'Тактическая версия с акцентом на боевую систему.',
             'srd_url': 'https://4e.dndsrd.com/'},
            {'name': 'Dungeons & Dragons Basic', 'slug': 'dnd-basic',
             'description': 'Оригинальная система 1974 года, предок всех современных НРИ.',
             'srd_url': 'https://www.dndadventurersleague.org/'},

            # Pathfinder
            {'name': 'Pathfinder 2nd Edition', 'slug': 'pathfinder2e',
             'description': 'Глубокая кастомизация, три действия за ход, современный дизайн.',
             'srd_url': 'https://2e.aonprd.com/'},
            {'name': 'Pathfinder 1st Edition', 'slug': 'pathfinder1e',
             'description': 'Улучшенный D&D 3.5 с исправлениями и расширениями.',
             'srd_url': 'https://www.d20pfsrd.com/'},

            # Warhammer
            {'name': 'Warhammer Fantasy Roleplay 4e', 'slug': 'warhammer-fantasy',
             'description': 'Мрачный низкофэнтези мир Старого Света. Карьеры и безумие.',
             'srd_url': 'https://cubicle7games.com/our-games/warhammer-fantasy-roleplay/'},
            {'name': 'Warhammer 40,000: Wrath & Glory', 'slug': 'warhammer40k',
             'description': 'Готический научно-фантастический хоррор в далеком будущем.',
             'srd_url': 'https://cubicle7games.com/our-games/warhammer-40000-wrath-glory/'},

            # Другие популярные системы
            {'name': 'Call of Cthulhu 7e', 'slug': 'cthulhu',
             'description': 'Хоррор-расследования по произведениям Лавкрафта. Механика безумия.',
             'srd_url': 'https://www.chaosium.com/call-of-cthulhu-rpg/'},
            {'name': 'Shadowrun 6e', 'slug': 'shadowrun',
             'description': 'Киберпанк с магией. Орки-хакеры, эльфы-уличные самураи.',
             'srd_url': 'https://www.shadowrunsrd.com/'},
            {'name': 'Starfinder', 'slug': 'starfinder',
             'description': 'Научная фантастика в стиле Pathfinder. Космические приключения.',
             'srd_url': 'https://starfinder.aonprd.com/'},
            {'name': 'Vampire: The Masquerade 5e', 'slug': 'vampire-v5',
             'description': 'Готический панк. Игра за вампиров в современном мире.',
             'srd_url': 'https://www.worldofdarkness.com/vampire-the-masquerade'},
            {'name': 'Cyberpunk RED', 'slug': 'cyberpunk',
             'description': 'Перезапуск классики киберпанка. Хай-тек, низкая жизнь.',
             'srd_url': 'https://rtalsoriangames.com/cyberpunk-red/'},

            # Универсальные системы
            {'name': 'GURPS 4e', 'slug': 'gurps',
             'description': 'Generic Universal RolePlaying System. Подходит для любого сеттинга.',
             'srd_url': 'https://www.sjgames.com/gurps/'},
            {'name': 'Fate Core', 'slug': 'fate',
             'description': 'Повествовательная система. Акцент на историю, а не на правила.',
             'srd_url': 'https://fate-srd.com/'},
            {'name': 'Savage Worlds Adventure Edition', 'slug': 'savage-worlds',
             'description': 'Быстрая, яростная и веселая система для любых жанров.',
             'srd_url': 'https://www.peginc.com/savage-worlds-adventure-edition/'},

            # Инди и альтернативные
            {'name': 'Blades in the Dark', 'slug': 'blades',
             'description': 'Игра за преступников в готическом городе. Механика напряжений и черт.',
             'srd_url': 'https://bladesinthedark.com/'},
            {'name': 'Apocalypse World', 'slug': 'apocalypse-world',
             'description': 'Постапокалипсис с акцентом на отношения между персонажами.',
             'srd_url': 'https://apocalypse-world.com/'},
            {'name': '13th Age', 'slug': '13th-age',
             'description': 'D20 система от создателей D&D 3e и 4e. Уникальные механики связей.',
             'srd_url': 'https://www.13thagesrd.com/'},
            {'name': 'Traveller', 'slug': 'traveller',
             'description': 'Классическая космическая опера. Жестокая генерация персонажей.',
             'srd_url': 'https://www.mongoosepublishing.com/traveller'},
            {'name': 'Legend of the Five Rings', 'slug': 'l5r',
             'description': 'Фэнтези-Япония с самураями, духами и сложной системой чести.',
             'srd_url': 'https://www.fantasyflightgames.com/en/products/legend-of-the-five-rings-roleplaying-game/'},
        ]

        for system_data in systems_data:
            cls.objects.get_or_create(
                slug=system_data['slug'],
                defaults={
                    'name': system_data['name'],
                    'description': system_data['description'],
                    'srd_url': system_data['srd_url'],
                    'is_active': True
                }
            )

    class Meta:
        verbose_name = 'Игровая система'
        verbose_name_plural = 'Игровые системы'
        ordering = ['name']

    def __str__(self):
        return self.name


class Scenario(models.Model):
    """Модель сценария приключения"""

    DIFFICULTY_CHOICES = [
        ('beginner', 'Новичок (1-3 уровень)'),
        ('intermediate', 'Опытный (4-10 уровень)'),
        ('advanced', 'Ветеран (11-16 уровень)'),
        ('expert', 'Мастер (17-20 уровень)'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('archived', 'В архиве'),
    ]

    title = models.CharField('Название сценария', max_length=200)
    description = models.TextField('Краткое описание', blank=True)
    content = models.TextField('Текст сценария')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    game_system = models.ForeignKey(GameSystem, on_delete=models.PROTECT, verbose_name='Игровая система')

    # Статистика и аналитика
    difficulty = models.CharField('Уровень сложности', max_length=20, choices=DIFFICULTY_CHOICES,
                                  default='intermediate')
    estimated_play_time = models.PositiveIntegerField('Примерное время игры (часы)', default=4)
    recommended_players = models.PositiveIntegerField('Рекомендуемое количество игроков', default=4)
    recommended_level = models.CharField('Рекомендуемый уровень персонажей', max_length=50, default='1-3')

    # Оценки аналитики
    combat_balance_score = models.FloatField('Оценка баланса боя', default=0.0,
                                             validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    puzzle_complexity_score = models.FloatField('Сложность загадок', default=0.0,
                                                validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    narrative_coherence = models.FloatField('Связность повествования', default=0.0,
                                            validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    # Метаданные
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='draft')
    is_public = models.BooleanField('Публичный доступ', default=False)
    tags = models.JSONField('Теги', default=list, blank=True)

    # Временные метки
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлен', auto_now=True)
    published_at = models.DateTimeField('Опубликован', null=True, blank=True)

    # Счетчики
    views = models.PositiveIntegerField('Просмотры', default=0)
    favorites = models.PositiveIntegerField('В избранном', default=0)

    class Meta:
        verbose_name = 'Сценарий'
        verbose_name_plural = 'Сценарии'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_public']),
            models.Index(fields=['game_system', 'difficulty']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Автоматическое обновление published_at при публикации"""
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def word_count(self):
        """Количество слов в сценарии"""
        return len(self.content.split())

    @property
    def reading_time(self):
        """Примерное время чтения в минутах"""
        return max(1, self.word_count // 200)  # 200 слов в минуту

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('scenario_detail', args=[str(self.id)])


class ScenarioElement(models.Model):
    """Структурированные элементы сценария"""

    ELEMENT_TYPES = [
        ('npc', 'NPC (Неигровой персонаж)'),
        ('location', 'Локация'),
        ('item', 'Предмет'),
        ('encounter', 'Боевая встреча'),
        ('puzzle', 'Загадка/Головоломка'),
        ('trap', 'Ловушка'),
        ('treasure', 'Сокровище'),
        ('clue', 'Зацепка/Подсказка'),
        ('event', 'Событие'),
        ('dialogue', 'Диалог'),
    ]

    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='elements',
                                 verbose_name='Сценарий')
    element_type = models.CharField('Тип элемента', max_length=20, choices=ELEMENT_TYPES)
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')

    # Позиция в тексте
    start_position = models.PositiveIntegerField('Начальная позиция в тексте')
    end_position = models.PositiveIntegerField('Конечная позиция в тексте')

    # Характеристики (JSON)
    attributes = models.JSONField('Атрибуты', default=dict, blank=True)

    # Сложность и баланс
    challenge_rating = models.FloatField('Уровень сложности (CR)', null=True, blank=True,
                                         validators=[MinValueValidator(0.0)])
    xp_value = models.PositiveIntegerField('Опыт за победу', null=True, blank=True)
    gold_value = models.PositiveIntegerField('Стоимость в золотых', null=True, blank=True)

    # Связи с другими элементами
    related_elements = models.ManyToManyField('self', blank=True, symmetrical=False,
                                              verbose_name='Связанные элементы')

    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Элемент сценария'
        verbose_name_plural = 'Элементы сценария'
        ordering = ['start_position']
        indexes = [
            models.Index(fields=['scenario', 'element_type']),
            models.Index(fields=['element_type', 'challenge_rating']),
        ]

    def __str__(self):
        return f"{self.get_element_type_display()}: {self.name}"

    @property
    def text_snippet(self):
        """Отрывок текста из сценария"""
        return self.scenario.content[self.start_position:self.end_position][:100] + "..."


class AnalysisResult(models.Model):
    """Результаты анализа сценария"""

    ANALYSIS_TYPES = [
        ('combat_balance', 'Баланс боев'),
        ('puzzle_analysis', 'Анализ загадок'),
        ('narrative_flow', 'Поток повествования'),
        ('element_extraction', 'Извлечение элементов'),
        ('recommendations', 'Рекомендации'),
    ]

    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='analyses',
                                 verbose_name='Сценарий')
    analysis_type = models.CharField('Тип анализа', max_length=50, choices=ANALYSIS_TYPES)

    # Результаты
    results = models.JSONField('Результаты анализа', default=dict)
    recommendations = models.JSONField('Рекомендации', default=list, blank=True)
    warnings = models.JSONField('Предупреждения', default=list, blank=True)

    # Метрики
    execution_time = models.FloatField('Время выполнения (сек)', default=0.0)
    confidence_score = models.FloatField('Уверенность анализа', default=0.0,
                                         validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    # Метаданные
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    analysis_version = models.CharField('Версия анализатора', max_length=50, default='1.0')

    class Meta:
        verbose_name = 'Результат анализа'
        verbose_name_plural = 'Результаты анализа'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['scenario', 'analysis_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_analysis_type_display()} для {self.scenario.title}"

    def get_recommendations_text(self):
        """Форматирование рекомендаций в текст"""
        return "\n".join([f"• {rec}" for rec in self.recommendations])


class UserProfile(models.Model):
    """Профиль пользователя"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile',
                                verbose_name='Пользователь')
    bio = models.TextField('О себе', blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', null=True, blank=True)
    favorite_systems = models.ManyToManyField(GameSystem, blank=True, verbose_name='Любимые системы')
    experience_level = models.CharField('Уровень опыта', max_length=20,
                                        choices=Scenario.DIFFICULTY_CHOICES, default='intermediate')

    # Настройки
    show_advanced_analytics = models.BooleanField('Показывать расширенную аналитику', default=True)
    receive_notifications = models.BooleanField('Получать уведомления', default=True)

    # Статистика
    scenarios_created = models.PositiveIntegerField('Создано сценариев', default=0)
    scenarios_published = models.PositiveIntegerField('Опубликовано сценариев', default=0)
    total_views = models.PositiveIntegerField('Всего просмотров', default=0)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлен', auto_now=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f"Профиль {self.user.username}"

    @property
    def display_name(self):
        """Имя для отображения"""
        return self.user.get_full_name() or self.user.username


class Favorite(models.Model):
    """Избранные сценарии пользователей"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites',
                             verbose_name='Пользователь')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='favorited_by',
                                 verbose_name='Сценарий')
    created_at = models.DateTimeField('Добавлен', auto_now_add=True)
    notes = models.TextField('Заметки', blank=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        unique_together = ['user', 'scenario']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.scenario.title}"
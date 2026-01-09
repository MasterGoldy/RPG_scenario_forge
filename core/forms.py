"""
Формы для RPG Scenario Forge.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator

from core.models import Scenario, ScenarioElement, UserProfile, GameSystem
import re


class UserRegisterForm(UserCreationForm):
    """Форма регистрации пользователя с минимальными проверками пароля"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Убираем все стандартные подсказки Django
        self.fields['password1'].help_text = "Минимум 8 символов"
        self.fields['password2'].help_text = "Введите пароль ещё раз"

        # Оставляем только валидатор минимальной длины
        self.fields['password1'].validators = [MinLengthValidator(8)]

    # Убираем стандартные проверки пароля Django
    def _post_clean(self):
        # Вызываем базовый метод ModelForm, пропуская UserCreationForm
        super(forms.ModelForm, self)._post_clean()

    # Упрощенная проверка пароля - только длина
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")

        # Проверяем только длину
        if len(password1) < 8:
            raise ValidationError(
                "Пароль должен содержать не менее 8 символов.",
                code='password_too_short',
            )

        return password1

    # Упрощенная проверка совпадения паролей
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError(
                "Пароли не совпадают.",
                code='password_mismatch',
            )

        return password2


class ScenarioForm(forms.ModelForm):
    """Форма создания/редактирования сценария"""

    tags_input = forms.CharField(
        required=False,
        label='Теги (через запятую)',
        widget=forms.TextInput(attrs={
            'placeholder': 'приключение, подземелье, драконы'
        })
    )

    class Meta:
        model = Scenario
        fields = [
            'title', 'description', 'content', 'game_system',
            'difficulty', 'estimated_play_time', 'recommended_players',
            'recommended_level', 'is_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название сценария'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание сценария'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Текст сценария...\n\nВы можете использовать специальные теги:\n[NPC: Имя] - для NPC\n[LOC: Название] - для локаций\n[ITEM: Предмет] - для предметов\n[ENCOUNTER: Название] - для боевых встреч'
            }),
            'game_system': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'estimated_play_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 48
            }),
            'recommended_players': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'recommended_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'например: 1-3 или 5, 7, 10'
            }),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_public': 'Сделать публичным',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем только активные игровые системы
        self.fields['game_system'].queryset = GameSystem.objects.filter(is_active=True)
        self.fields['game_system'].empty_label = "Выберите игровую систему"

    def clean_content(self):
        """Валидация текста сценария"""
        content = self.cleaned_data.get('content')

        if len(content.strip()) < 100:
            raise ValidationError('Текст сценария должен содержать минимум 100 символов.')

        if len(content.strip()) > 50000:
            raise ValidationError('Текст сценария не должен превышать 50,000 символов.')

        return content

    def clean_recommended_level(self):
        """Валидация рекомендуемого уровня"""
        level = self.cleaned_data.get('recommended_level')

        # Проверяем формат: либо диапазон (1-3), либо конкретные уровни (5, 7, 10)
        if not re.match(r'^(\d+(-\d+)?|\d+(,\s*\d+)*)$', level):
            raise ValidationError('Введите уровни в формате "1-3" или "5, 7, 10"')

        return level


class ScenarioElementForm(forms.ModelForm):
    """Форма для редактирования элементов сценария"""

    class Meta:
        model = ScenarioElement
        fields = ['element_type', 'name', 'description', 'challenge_rating', 'xp_value', 'gold_value']
        widgets = {
            'element_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'challenge_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.25',
                'min': '0'
            }),
            'xp_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'gold_value': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class AnalysisSettingsForm(forms.Form):
    """Форма настройки параметров анализа"""

    extract_elements = forms.BooleanField(
        initial=True,
        required=False,
        label='Извлекать элементы сценария',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    analyze_combat = forms.BooleanField(
        initial=True,
        required=False,
        label='Анализировать баланс боев',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    analyze_puzzles = forms.BooleanField(
        initial=True,
        required=False,
        label='Анализировать загадки',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    check_narrative = forms.BooleanField(
        initial=True,
        required=False,
        label='Проверять связность повествования',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    generate_recommendations = forms.BooleanField(
        initial=True,
        required=False,
        label='Генерировать рекомендации',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    party_level = forms.IntegerField(
        initial=3,
        min_value=1,
        max_value=20,
        label='Уровень группы игроков',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    party_size = forms.IntegerField(
        initial=4,
        min_value=1,
        max_value=10,
        label='Количество игроков',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""

    class Meta:
        model = UserProfile
        fields = ['bio', 'experience_level', 'show_advanced_analytics', 'receive_notifications']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе, вашем опыте в НРИ...'
            }),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'show_advanced_analytics': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receive_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        """Сохранение профиля и данных пользователя"""
        profile = super().save(commit=False)

        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            self.user.save()

        if commit:
            profile.save()
            self.save_m2m()

        return profile


class SearchForm(forms.Form):
    """Форма поиска сценариев"""

    query = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию, описанию...'
        })
    )

    game_system = forms.ModelChoiceField(
        queryset=GameSystem.objects.filter(is_active=True),
        required=False,
        label='Игровая система',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    difficulty = forms.ChoiceField(
        choices=[('', 'Любая сложность')] + Scenario.DIFFICULTY_CHOICES,
        required=False,
        label='Сложность',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    min_play_time = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=48,
        label='Минимальное время игры (часы)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    max_play_time = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=48,
        label='Максимальное время игры (часы)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Новые сначала'),
            ('created_at', 'Старые сначала'),
            ('-views', 'Популярные'),
            ('-favorites', 'По избранным'),
            ('title', 'По названию (А-Я)'),
        ],
        required=False,
        label='Сортировка',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        """Валидация временных интервалов"""
        cleaned_data = super().clean()
        min_time = cleaned_data.get('min_play_time')
        max_time = cleaned_data.get('max_play_time')

        if min_time and max_time and min_time > max_time:
            raise ValidationError('Минимальное время не может быть больше максимального.')

        return cleaned_data


class RegisterForm(UserCreationForm):
    """Форма регистрации"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя пользователя'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Подтверждение пароля'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже зарегистрирован')
        return email


class LoginForm(AuthenticationForm):
    """Форма входа"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя пользователя'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
    )
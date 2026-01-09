"""
Утилиты для RPG Scenario Forge.
"""

import re
import json
import time
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import requests
from django.conf import settings


class TextAnalyzer:
    """Анализатор текста сценариев"""

    # Паттерны для извлечения элементов
    PATTERNS = {
        'npc': [
            r'\[NPC:\s*([^\]]+)\]',  # [NPC: Имя]
            r'(?:NPC|персонаж)[:\s]+([A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*)',
            r'(?:имя|зовут|называется)[:\s]+([A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*)',
        ],
        'location': [
            r'\[LOC:\s*([^\]]+)\]',
            r'(?:локация|место|город|деревня|пещера)[:\s]+([A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*)',
            r'в\s+([A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*)',
        ],
        'item': [
            r'\[ITEM:\s*([^\]]+)\]',
            r'(?:предмет|артефакт|оружие|доспех)[:\s]+([A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*)',
            r'(?:магический|волшебный)\s+([a-zа-я]+)',
        ],
        'encounter': [
            r'\[ENCOUNTER:\s*([^\]]+)\]',
            r'(?:встреча|бой|сражение)[:\s]+([A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*)',
            r'(?:против|противник|враг)[:\s]+([A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*)',
        ],
        'puzzle': [
            r'\[PUZZLE:\s*([^\]]+)\]',
            r'(?:загадка|головоломка|тайна)[:\s]+([A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*)',
            r'(?:решить|разгадать|открыть)[:\s]+([a-zа-я]+)',
        ]
    }

    def __init__(self):
        self.cache = {}

    def extract_elements(self, text: str) -> Dict[str, List[Dict]]:
        """
        Извлечение элементов из текста сценария.

        Args:
            text: Текст сценария

        Returns:
            Словарь с извлеченными элементами по типам
        """
        if text in self.cache:
            return self.cache[text]

        elements = defaultdict(list)

        for element_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    element_name = match.group(1).strip()
                    if element_name and len(element_name) > 1:
                        element = {
                            'name': element_name,
                            'start_pos': match.start(),
                            'end_pos': match.end(),
                            'text': match.group(0),
                            'confidence': 0.8 if '[' in match.group(0) else 0.5,
                        }
                        elements[element_type].append(element)

        # Удаление дубликатов
        for element_type in elements:
            seen = set()
            unique_elements = []
            for elem in elements[element_type]:
                key = (elem['name'], elem['start_pos'])
                if key not in seen:
                    seen.add(key)
                    unique_elements.append(elem)
            elements[element_type] = unique_elements

        self.cache[text] = dict(elements)
        return dict(elements)

    def calculate_text_metrics(self, text: str) -> Dict:
        """Расчет метрик текста"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Убираем пустые строки
        sentences = [s.strip() for s in sentences if s.strip()]

        metrics = {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'unique_words': len(set(words)),
            'lexical_diversity': len(set(words)) / max(len(words), 1),
        }

        return metrics


class CombatBalanceAnalyzer:
    """Анализатор баланса боевых столкновений"""

    # XP thresholds по уровням (D&D 5e)
    XP_THRESHOLDS = {
        1: {'easy': 25, 'medium': 50, 'hard': 75, 'deadly': 100},
        2: {'easy': 50, 'medium': 100, 'hard': 150, 'deadly': 200},
        3: {'easy': 75, 'medium': 150, 'hard': 225, 'deadly': 400},
        4: {'easy': 125, 'medium': 250, 'hard': 375, 'deadly': 500},
        5: {'easy': 250, 'medium': 500, 'hard': 750, 'deadly': 1100},
        6: {'easy': 300, 'medium': 600, 'hard': 900, 'deadly': 1400},
        7: {'easy': 350, 'medium': 750, 'hard': 1100, 'deadly': 1700},
        8: {'easy': 450, 'medium': 900, 'hard': 1400, 'deadly': 2100},
        9: {'easy': 550, 'medium': 1100, 'hard': 1600, 'deadly': 2400},
        10: {'easy': 600, 'medium': 1200, 'hard': 1900, 'deadly': 2800},
        11: {'easy': 800, 'medium': 1600, 'hard': 2400, 'deadly': 3600},
        12: {'easy': 1000, 'medium': 2000, 'hard': 3000, 'deadly': 4500},
        13: {'easy': 1100, 'medium': 2200, 'hard': 3400, 'deadly': 5100},
        14: {'easy': 1250, 'medium': 2500, 'hard': 3800, 'deadly': 5700},
        15: {'easy': 1400, 'medium': 2800, 'hard': 4300, 'deadly': 6400},
        16: {'easy': 1600, 'medium': 3200, 'hard': 4800, 'deadly': 7200},
        17: {'easy': 1850, 'medium': 3700, 'hard': 5500, 'deadly': 8300},
        18: {'easy': 2100, 'medium': 4200, 'hard': 6300, 'deadly': 9500},
        19: {'easy': 2400, 'medium': 4900, 'hard': 7300, 'deadly': 10900},
        20: {'easy': 2800, 'medium': 5700, 'hard': 8500, 'deadly': 12700},
    }

    # Множители за количество монстров
    MONSTER_MULTIPLIERS = {
        1: 1.0,
        2: 1.5,
        3: 2.0,
        4: 2.0,
        5: 2.0,
        6: 2.0,
        7: 2.5,
        8: 2.5,
        9: 2.5,
        10: 2.5,
        11: 3.0,
        12: 3.0,
        13: 3.0,
        14: 3.0,
        15: 4.0,
    }

    # Базовый XP за CR (D&D 5e)
    XP_BY_CR = {
        0: 0, 0.125: 25, 0.25: 50, 0.5: 100,
        1: 200, 2: 450, 3: 700, 4: 1100,
        5: 1800, 6: 2300, 7: 2900, 8: 3900,
        9: 5000, 10: 5900, 11: 7200, 12: 8400,
        13: 10000, 14: 11500, 15: 13000, 16: 15000,
        17: 18000, 18: 20000, 19: 22000, 20: 25000,
        21: 33000, 22: 41000, 23: 50000, 24: 62000,
        25: 75000, 26: 90000, 27: 105000, 28: 120000,
        29: 135000, 30: 155000
    }

    def __init__(self):
        self.cache = {}

    def calculate_encounter_difficulty(self, monsters: list, party_level: int, party_size: int) -> dict:
        """
        Расчет сложности боевой встречи по правилам D&D 5e.

        Args:
            monsters: Список монстров с CR и количеством
            party_level: Уровень группы
            party_size: Количество игроков

        Returns:
            Словарь с результатами анализа
        """
        cache_key = f"{hash(str(monsters))}_{party_level}_{party_size}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 1. Рассчитываем базовый XP за каждого монстра
        total_base_xp = 0
        total_monsters = 0

        for monster in monsters:
            cr = monster.get('cr', 0)
            quantity = monster.get('quantity', 1)
            monster_xp = self.XP_BY_CR.get(cr, 0)
            total_base_xp += monster_xp * quantity
            total_monsters += quantity

        # 2. Применяем множитель за количество монстров
        multiplier = self.MONSTER_MULTIPLIERS.get(total_monsters, 4.0)
        adjusted_xp = total_base_xp * multiplier

        # 3. Рассчитываем пороги сложности для группы
        party_xp_thresholds = self._calculate_party_thresholds(party_level, party_size)

        # 4. Определяем сложность встречи
        difficulty = self._determine_difficulty(adjusted_xp, party_xp_thresholds)

        # 5. Рассчитываем балансный балл (0-1)
        balance_score = self._calculate_balance_score(adjusted_xp, party_xp_thresholds)

        # 6. Генерируем рекомендации
        recommendations = self._generate_recommendations(
            monsters, total_monsters, adjusted_xp,
            party_xp_thresholds, difficulty
        )

        result = {
            'total_monsters': total_monsters,
            'total_base_xp': total_base_xp,
            'multiplier': multiplier,
            'adjusted_xp': adjusted_xp,
            'party_xp_thresholds': party_xp_thresholds,
            'difficulty': difficulty,
            'balance_score': round(balance_score, 3),
            'recommendations': recommendations,
            'monster_analysis': self._analyze_monster_composition(monsters),
        }

        self.cache[cache_key] = result
        return result

    def _calculate_party_thresholds(self, party_level: int, party_size: int) -> dict:
        """Рассчитывает пороги XP для всей группы"""
        level_thresholds = self.XP_THRESHOLDS.get(party_level, self.XP_THRESHOLDS[20])

        return {
            'easy': level_thresholds['easy'] * party_size,
            'medium': level_thresholds['medium'] * party_size,
            'hard': level_thresholds['hard'] * party_size,
            'deadly': level_thresholds['deadly'] * party_size,
        }

    def _determine_difficulty(self, adjusted_xp: float, thresholds: dict) -> str:
        """Определяет сложность встречи"""
        if adjusted_xp <= thresholds['easy']:
            return 'Легкая'
        elif adjusted_xp <= thresholds['medium']:
            return 'Средняя'
        elif adjusted_xp <= thresholds['hard']:
            return 'Сложная'
        elif adjusted_xp <= thresholds['deadly']:
            return 'Опасная'
        else:
            return 'Смертельная'

    def _calculate_balance_score(self, adjusted_xp: float, thresholds: dict) -> float:
        """Рассчитывает балансный балл (0-1, где 0.5 - идеальный баланс)"""
        # Идеальный баланс - между medium и hard
        ideal_min = thresholds['medium'] * 0.8
        ideal_max = thresholds['hard'] * 1.2

        if ideal_min <= adjusted_xp <= ideal_max:
            return 0.5  # Идеальный баланс
        elif adjusted_xp < thresholds['easy']:
            # Слишком легко - чем дальше от easy, тем хуже
            distance = (thresholds['easy'] - adjusted_xp) / thresholds['easy']
            return max(0.0, 0.5 - distance * 0.5)
        elif adjusted_xp > thresholds['deadly']:
            # Слишком сложно - чем дальше от deadly, тем хуже
            distance = (adjusted_xp - thresholds['deadly']) / thresholds['deadly']
            return max(0.0, 0.5 - min(distance * 0.5, 0.5))
        else:
            # В пределах нормальной сложности
            if adjusted_xp < thresholds['medium']:
                # Между easy и medium
                range_size = thresholds['medium'] - thresholds['easy']
                position = (adjusted_xp - thresholds['easy']) / range_size
                return 0.25 + position * 0.25
            else:
                # Между medium и deadly
                range_size = thresholds['deadly'] - thresholds['medium']
                position = (adjusted_xp - thresholds['medium']) / range_size
                return 0.5 + position * 0.25

    def _analyze_monster_composition(self, monsters: list) -> dict:
        """Анализирует состав монстров"""
        if not monsters:
            return {'total_count': 0, 'cr_distribution': {}, 'analysis': 'Нет монстров'}

        total_count = sum(m.get('quantity', 1) for m in monsters)
        cr_values = []

        for monster in monsters:
            cr = monster.get('cr', 0)
            quantity = monster.get('quantity', 1)
            cr_values.extend([cr] * quantity)

        # Статистика по CR
        cr_counter = {}
        for cr in cr_values:
            cr_counter[cr] = cr_counter.get(cr, 0) + 1

        # Средний CR
        avg_cr = sum(cr_values) / len(cr_values) if cr_values else 0

        # Анализ разнообразия
        diversity_score = len(set(cr_values)) / len(cr_values) if cr_values else 0

        return {
            'total_count': total_count,
            'avg_cr': round(avg_cr, 2),
            'cr_distribution': dict(sorted(cr_counter.items())),
            'diversity_score': round(diversity_score, 3),
            'min_cr': min(cr_values) if cr_values else 0,
            'max_cr': max(cr_values) if cr_values else 0,
        }

    def _generate_recommendations(self, monsters: list, total_monsters: int,
                                  adjusted_xp: float, thresholds: dict, difficulty: str) -> list:
        """Генерирует рекомендации по балансу"""
        recommendations = []

        if total_monsters == 0:
            recommendations.append("Добавьте боевую встречу для более динамичного геймплея")
            return recommendations

        # Анализ количества монстров
        if total_monsters == 1:
            recommendations.append("Одинокий монстр может быть быстро убит - добавьте поддержку")
        elif total_monsters > 6:
            recommendations.append("Слишком много монстров - игра может замедлиться, объедините некоторых")

        # Анализ сложности
        if difficulty in ['Легкая', 'Средняя']:
            recommendations.append("Можно усилить встречу для большего вызова")
        elif difficulty in ['Опасная', 'Смертельная']:
            recommendations.append("Встреча может быть слишком сложной для группы")

        # Анализ разнообразия CR
        cr_values = []
        for monster in monsters:
            cr = monster.get('cr', 0)
            quantity = monster.get('quantity', 1)
            cr_values.extend([cr] * quantity)

        unique_crs = len(set(cr_values))
        if unique_crs == 1 and total_monsters > 3:
            recommendations.append("Добавьте монстров разного CR для тактического разнообразия")

        # Проверка на наличие лидера
        max_cr = max(cr_values) if cr_values else 0
        if max_cr <= 1 and total_monsters > 2:
            recommendations.append("Добавьте сильного монстра-лидера для тактической глубины")

        return recommendations

    def extract_monsters_from_text(self, text: str) -> list:
        """
        Извлекает информацию о монстрах из текста.

        Args:
            text: Текст сценария

        Returns:
            Список монстров с CR и количеством
        """
        monsters = []

        # Паттерны для извлечения монстров
        patterns = [
            # [MONSTER: Гоблин x3 CR 1/4]
            r'\[MONSTER:\s*([^\]]+?)\s*(?:x\s*(\d+))?\s*(?:CR\s*([\d/\.]+))?\]',
            # Гоблины (x3, CR 1/4)
            r'([A-ZА-Я][a-zа-я]+(?:ы|и|а)?)\s*\(?(?:x\s*(\d+))?\s*,?\s*(?:CR\s*([\d/\.]+))?\)?',
            # 3 гоблина (CR 0.25)
            r'(\d+)\s+([a-zа-я]+(?:ов|ев|ей)?)\s*\(?(?:CR\s*([\d/\.]+))?\)?',
        ]

        # Известные монстры D&D 5e с их CR
        KNOWN_MONSTERS = {
            'гоблин': 0.25, 'goblin': 0.25,
            'орк': 0.5, 'ork': 0.5, 'orc': 0.5,
            'волк': 0.25, 'wolf': 0.25,
            'медведь': 2, 'bear': 2,
            'тролль': 5, 'troll': 5,
            'дракон': 10, 'dragon': 10,
            'зомби': 0.25, 'zombie': 0.25,
            'скелет': 0.25, 'skeleton': 0.25,
            'вампир': 13, 'vampire': 13,
            'демон': 8, 'demon': 8,
            'дьявол': 6, 'devil': 6,
            'элементаль': 5, 'elemental': 5,
        }

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                monster_name = match.group(1) or match.group(2)
                quantity = match.group(2) or 1
                cr_from_text = match.group(3)

                if monster_name:
                    # Очистка названия
                    monster_name = monster_name.strip().lower()

                    # Определяем CR
                    cr = 0
                    if cr_from_text:
                        try:
                            if '/' in cr_from_text:
                                num, denom = cr_from_text.split('/')
                                cr = float(num) / float(denom)
                            else:
                                cr = float(cr_from_text)
                        except ValueError:
                            cr = KNOWN_MONSTERS.get(monster_name, 0.5)
                    else:
                        # Ищем в известных монстрах
                        for known_name, known_cr in KNOWN_MONSTERS.items():
                            if known_name in monster_name:
                                cr = known_cr
                                break
                        else:
                            cr = 0.5  # Дефолтный CR

                    # Преобразуем количество
                    try:
                        quantity = int(quantity)
                    except (ValueError, TypeError):
                        quantity = 1

                    monsters.append({
                        'name': monster_name.title(),
                        'quantity': quantity,
                        'cr': cr,
                        'xp': self.XP_BY_CR.get(cr, 0),
                        'source': match.group(0),
                    })

        # Удаление дубликатов
        unique_monsters = []
        seen = set()

        for monster in monsters:
            key = (monster['name'], monster['cr'])
            if key not in seen:
                seen.add(key)
                unique_monsters.append(monster)

        return unique_monsters


class PuzzleAnalyzer:
    """Анализатор сложности загадок и головоломок"""

    def __init__(self):
        self.complexity_keywords = {
            'easy': ['простой', 'легкий', 'очевидный', 'прямой', 'ясный'],
            'medium': ['средний', 'умеренный', 'логичный', 'стандартный', 'типичный'],
            'hard': ['сложный', 'трудный', 'запутанный', 'хитрый', 'замысловатый'],
            'expert': ['экспертный', 'головоломный', 'загадочный', 'неочевидный', 'скрытый'],
        }

        self.solution_patterns = [
            (r'(?:решение|ответ|ключ)[:\s]+([^\.]+)', 0.8),
            (r'(?:чтобы решить|для решения)[^\.]+?([^\.]+)', 0.6),
            (r'(?:подсказка|намёк)[:\s]+([^\.]+)', 0.4),
        ]

    def analyze_puzzle_complexity(self, puzzle_text: str) -> dict:
        """
        Анализирует сложность загадки.

        Args:
            puzzle_text: Текст загадки

        Returns:
            Словарь с результатами анализа
        """
        if not puzzle_text.strip():
            return {'complexity_score': 0, 'level': 'Нет загадки', 'recommendations': []}

        metrics = self._calculate_text_metrics(puzzle_text)
        keyword_score = self._analyze_keywords(puzzle_text)
        structure_score = self._analyze_structure(puzzle_text)
        solution_clarity = self._analyze_solution_clarity(puzzle_text)

        # Итоговый балл сложности (0-1)
        complexity_score = (
                metrics['lexical_diversity'] * 0.3 +
                keyword_score * 0.3 +
                structure_score * 0.2 +
                (1 - solution_clarity) * 0.2  # Чем яснее решение, тем проще загадка
        )

        # Определяем уровень сложности
        if complexity_score < 0.25:
            level = 'Очень простой'
        elif complexity_score < 0.45:
            level = 'Простой'
        elif complexity_score < 0.65:
            level = 'Средний'
        elif complexity_score < 0.85:
            level = 'Сложный'
        else:
            level = 'Очень сложный'

        # Генерируем рекомендации
        recommendations = self._generate_puzzle_recommendations(
            complexity_score, metrics, solution_clarity
        )

        return {
            'complexity_score': round(complexity_score, 3),
            'level': level,
            'metrics': metrics,
            'keyword_score': round(keyword_score, 3),
            'structure_score': round(structure_score, 3),
            'solution_clarity': round(solution_clarity, 3),
            'recommendations': recommendations,
            'word_count': metrics['word_count'],
        }

    def _calculate_text_metrics(self, text: str) -> dict:
        """Рассчитывает метрики текста загадки"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Считаем вопросы
        question_count = len([s for s in sentences if s.endswith('?')])

        # Считаем сложные слова (длиннее 7 букв)
        complex_words = [w for w in words if len(w) > 7]

        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'question_count': question_count,
            'avg_word_length': sum(len(w) for w in words) / max(len(words), 1),
            'complex_word_ratio': len(complex_words) / max(len(words), 1),
            'lexical_diversity': len(set(words)) / max(len(words), 1),
            'question_ratio': question_count / max(len(sentences), 1),
        }

    def _analyze_keywords(self, text: str) -> float:
        """Анализирует ключевые слова сложности"""
        text_lower = text.lower()
        scores = []

        for level, keywords in self.complexity_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if level == 'easy':
                scores.append(matches * 0.25)
            elif level == 'medium':
                scores.append(matches * 0.5)
            elif level == 'hard':
                scores.append(matches * 0.75)
            else:  # expert
                scores.append(matches * 1.0)

        return min(sum(scores) / 10, 1.0)  # Нормализуем до 0-1

    def _analyze_structure(self, text: str) -> float:
        """Анализирует структурную сложность"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        # Длина предложений
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # Вариативность длины предложений
        sentence_lengths = [len(s.split()) for s in sentences]
        if len(sentence_lengths) > 1:
            length_variance = sum((l - avg_sentence_length) ** 2 for l in sentence_lengths) / len(sentence_lengths)
        else:
            length_variance = 0

        # Оценка структуры (0-1)
        structure_score = (
                min(avg_sentence_length / 20, 1.0) * 0.4 +  # Длина предложений
                min(length_variance / 50, 1.0) * 0.3 +  # Вариативность
                (1 if any('?' in s for s in sentences) else 0.5) * 0.3  # Наличие вопросов
        )

        return min(structure_score, 1.0)

    def _analyze_solution_clarity(self, text: str) -> float:
        """Анализирует ясность решения"""
        text_lower = text.lower()

        # Проверяем наличие явных указаний на решение
        has_solution_mention = any(
            phrase in text_lower
            for phrase in ['решение', 'ответ', 'ключ', 'разгадка']
        )

        # Проверяем паттерны решений
        solution_pattern_score = 0
        for pattern, weight in self.solution_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                solution_pattern_score = max(solution_pattern_score, weight)

        # Проверяем наличие подсказок
        has_hints = any(
            hint in text_lower
            for hint in ['подсказка', 'намёк', 'улика', 'след']
        )

        clarity_score = (
                (1.0 if has_solution_mention else 0.3) * 0.4 +
                solution_pattern_score * 0.4 +
                (0.8 if has_hints else 0.2) * 0.2
        )

        return min(clarity_score, 1.0)

    def _generate_puzzle_recommendations(self, complexity_score: float,
                                         metrics: dict, solution_clarity: float) -> list:
        """Генерирует рекомендации по загадке"""
        recommendations = []

        # Рекомендации по сложности
        if complexity_score < 0.3:
            recommendations.append("Загадка слишком простая - добавьте больше деталей или усложните логику")
        elif complexity_score > 0.8:
            recommendations.append("Загадка может быть слишком сложной - добавьте подсказки")

        # Рекомендации по структуре
        if metrics['word_count'] < 50:
            recommendations.append("Загадка слишком короткая - раскройте детали")
        elif metrics['word_count'] > 300:
            recommendations.append("Загадка слишком длинная - упростите описание")

        if metrics['question_ratio'] < 0.1:
            recommendations.append("Добавьте наводящие вопросы для вовлечения игроков")

        # Рекомендации по ясности решения
        if solution_clarity < 0.3:
            recommendations.append("Решение неочевидно - добавьте больше подсказок")
        elif solution_clarity > 0.8:
            recommendations.append("Решение слишком очевидно - сделайте его более загадочным")

        return recommendations


class NarrativeAnalyzer:
    """Анализатор связности повествования"""

    def __init__(self):
        self.transition_words = [
            'затем', 'потом', 'после этого', 'вдруг', 'внезапно',
            'однако', 'но', 'тем не менее', 'следовательно', 'поэтому',
            'таким образом', 'кроме того', 'более того', 'в то же время',
        ]

        self.plot_elements = [
            'завязка', 'развитие', 'кульминация', 'развязка',
            'конфликт', 'разрешение', 'поворот', 'открытие',
        ]

    def analyze_narrative_flow(self, text: str) -> dict:
        """
        Анализирует связность повествования.

        Args:
            text: Текст сценария

        Returns:
            Словарь с результатами анализа
        """
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        sentences = self._split_into_sentences(text)

        coherence_score = self._calculate_coherence_score(paragraphs, sentences)
        pacing_score = self._analyze_pacing(paragraphs)
        structure_score = self._analyze_structure(text)

        # Итоговый балл связности (0-1)
        narrative_score = (
                coherence_score * 0.4 +
                pacing_score * 0.3 +
                structure_score * 0.3
        )

        # Генерируем рекомендации
        recommendations = self._generate_narrative_recommendations(
            narrative_score, len(paragraphs), len(sentences)
        )

        return {
            'narrative_score': round(narrative_score, 3),
            'coherence_score': round(coherence_score, 3),
            'pacing_score': round(pacing_score, 3),
            'structure_score': round(structure_score, 3),
            'paragraph_count': len(paragraphs),
            'sentence_count': len(sentences),
            'avg_paragraph_length': sum(len(p.split()) for p in paragraphs) / max(len(paragraphs), 1),
            'transition_word_count': self._count_transition_words(text),
            'recommendations': recommendations,
        }

    def _split_into_sentences(self, text: str) -> list:
        """Разделяет текст на предложения"""
        # Простой сплиттер, можно заменить на более сложный
        sentences = []
        current = []

        for char in text:
            current.append(char)
            if char in '.!?':
                sentence = ''.join(current).strip()
                if sentence:
                    sentences.append(sentence)
                current = []

        # Добавляем последнее предложение, если есть
        if current:
            sentence = ''.join(current).strip()
            if sentence:
                sentences.append(sentence)

        return sentences

    def _calculate_coherence_score(self, paragraphs: list, sentences: list) -> float:
        """Рассчитывает оценку связности"""
        if len(paragraphs) < 2 or len(sentences) < 4:
            return 0.5

        # Проверяем переходы между параграфами
        paragraph_coherence = 0
        for i in range(len(paragraphs) - 1):
            # Простая проверка: последнее слово предыдущего параграфа
            # и первое слово следующего параграфа
            prev_words = paragraphs[i].split()
            next_words = paragraphs[i + 1].split()

            if prev_words and next_words:
                # Проверяем наличие общих слов
                common_words = set(prev_words[-3:]) & set(next_words[:3])
                if common_words:
                    paragraph_coherence += 1

        paragraph_score = paragraph_coherence / max(len(paragraphs) - 1, 1)

        # Проверяем переходы между предложениями
        transition_count = 0
        for sentence in sentences:
            for transition in self.transition_words:
                if transition in sentence.lower():
                    transition_count += 1

        transition_score = min(transition_count / len(sentences), 1.0)

        return (paragraph_score * 0.6 + transition_score * 0.4)

    def _analyze_pacing(self, paragraphs: list) -> float:
        """Анализирует темп повествования"""
        if len(paragraphs) < 3:
            return 0.5

        # Анализируем длину параграфов
        paragraph_lengths = [len(p.split()) for p in paragraphs]
        avg_length = sum(paragraph_lengths) / len(paragraph_lengths)

        # Рассчитываем вариативность
        variance = sum((l - avg_length) ** 2 for l in paragraph_lengths) / len(paragraph_lengths)

        # Идеальный темп - умеренная вариативность
        if variance < 50:
            # Слишком однообразно
            pacing_score = 0.4
        elif variance < 200:
            # Хороший темп
            pacing_score = 0.8
        else:
            # Слишком изменчиво
            pacing_score = 0.5

        return pacing_score

    def _analyze_structure(self, text: str) -> float:
        """Анализирует структуру повествования"""
        text_lower = text.lower()

        # Проверяем наличие элементов сюжета
        plot_element_count = sum(1 for element in self.plot_elements if element in text_lower)

        # Проверяем наличие введения и заключения
        has_introduction = any(word in text_lower[:200]
                               for word in ['введение', 'начало', 'пролог'])
        has_conclusion = any(word in text_lower[-200:]
                             for word in ['заключение', 'конец', 'эпилог'])

        structure_score = (
                min(plot_element_count / 4, 1.0) * 0.4 +
                (1.0 if has_introduction else 0.5) * 0.3 +
                (1.0 if has_conclusion else 0.5) * 0.3
        )

        return structure_score

    def _count_transition_words(self, text: str) -> int:
        """Считает слова-переходы"""
        text_lower = text.lower()
        count = 0

        for word in self.transition_words:
            count += text_lower.count(word)

        return count

    def _generate_narrative_recommendations(self, narrative_score: float,
                                            paragraph_count: int, sentence_count: int) -> list:
        """Генерирует рекомендации по повествованию"""
        recommendations = []

        if narrative_score < 0.4:
            recommendations.append("Повествование требует улучшения связности")

        if paragraph_count < 3:
            recommendations.append("Добавьте больше параграфов для структурирования текста")
        elif paragraph_count > 20:
            recommendations.append("Слишком много коротких параграфов - объедините некоторые")

        if sentence_count < 10:
            recommendations.append("Добавьте деталей и описаний")

        if self._count_transition_words:
            recommendations.append("Используйте больше слов-переходов для связности")

        return recommendations


class DnDAPI:
    """Интеграция с D&D 5e API"""

    BASE_URL = "https://www.dnd5eapi.co/api"

    def __init__(self):
        self.cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RPG Scenario Forge/1.0',
            'Accept': 'application/json',
        })

    def get_monster_info(self, monster_name: str) -> dict:
        """
        Получает информацию о монстре из D&D 5e API.

        Args:
            monster_name: Название монстра (англ.)

        Returns:
            Словарь с информацией о монстре
        """
        cache_key = f"monster_{monster_name.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = self.session.get(f"{self.BASE_URL}/monsters/{monster_name.lower()}")

            if response.status_code == 200:
                data = response.json()
                result = {
                    'name': data.get('name', monster_name),
                    'challenge_rating': data.get('challenge_rating', 0),
                    'xp': data.get('xp', 0),
                    'type': data.get('type', ''),
                    'size': data.get('size', ''),
                    'armor_class': data.get('armor_class', 0),
                    'hit_points': data.get('hit_points', 0),
                    'speed': data.get('speed', {}),
                    'abilities': {
                        'str': data.get('strength', 10),
                        'dex': data.get('dexterity', 10),
                        'con': data.get('constitution', 10),
                        'int': data.get('intelligence', 10),
                        'wis': data.get('wisdom', 10),
                        'cha': data.get('charisma', 10),
                    },
                    'actions': data.get('actions', []),
                    'special_abilities': data.get('special_abilities', []),
                    'found': True,
                }
            else:
                result = {
                    'name': monster_name,
                    'challenge_rating': 0.5,
                    'xp': 100,
                    'found': False,
                    'error': f"Monster not found: {response.status_code}",
                }

        except Exception as e:
            result = {
                'name': monster_name,
                'challenge_rating': 0.5,
                'xp': 100,
                'found': False,
                'error': str(e),
            }

        self.cache[cache_key] = result
        return result

    def validate_monster_cr(self, monster_name: str, claimed_cr: float) -> dict:
        """
        Проверяет CR монстра через API.

        Args:
            monster_name: Название монстра
            claimed_cr: Заявленный CR

        Returns:
            Словарь с результатами валидации
        """
        api_data = self.get_monster_info(monster_name)

        if not api_data['found']:
            return {
                'valid': False,
                'message': 'Монстр не найден в базе D&D 5e',
                'suggested_cr': claimed_cr,
            }

        api_cr = api_data['challenge_rating']
        cr_difference = abs(api_cr - claimed_cr)

        if cr_difference < 0.25:
            return {
                'valid': True,
                'message': 'CR соответствует D&D 5e SRD',
                'api_cr': api_cr,
                'claimed_cr': claimed_cr,
            }
        else:
            return {
                'valid': False,
                'message': f'CR отличается от D&D 5e SRD ({api_cr} vs {claimed_cr})',
                'api_cr': api_cr,
                'claimed_cr': claimed_cr,
                'suggestion': f'Используйте CR {api_cr} для баланса',
            }

    def search_monsters_by_cr(self, min_cr: float = 0, max_cr: float = 30) -> list:
        """
        Ищет монстров по диапазону CR.

        Args:
            min_cr: Минимальный CR
            max_cr: Максимальный CR

        Returns:
            Список монстров
        """
        cache_key = f"monsters_cr_{min_cr}_{max_cr}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = self.session.get(f"{self.BASE_URL}/monsters")
            if response.status_code == 200:
                all_monsters = response.json().get('results', [])

                # Фильтруем по CR (нужно получить детали для каждого)
                filtered_monsters = []
                for monster in all_monsters[:50]:  # Ограничиваем для скорости
                    monster_details = self.get_monster_info(monster['index'])
                    if monster_details['found']:
                        cr = monster_details['challenge_rating']
                        if min_cr <= cr <= max_cr:
                            filtered_monsters.append({
                                'name': monster_details['name'],
                                'cr': cr,
                                'xp': monster_details['xp'],
                                'type': monster_details['type'],
                                'size': monster_details['size'],
                            })

                self.cache[cache_key] = filtered_monsters
                return filtered_monsters
            else:
                return []

        except Exception:
            return []

    def get_spell_info(self, spell_name: str) -> dict:
        """Получает информацию о заклинании"""
        cache_key = f"spell_{spell_name.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = self.session.get(f"{self.BASE_URL}/spells/{spell_name.lower()}")
            if response.status_code == 200:
                data = response.json()
                result = {
                    'name': data.get('name', spell_name),
                    'level': data.get('level', 0),
                    'school': data.get('school', {}).get('name', ''),
                    'casting_time': data.get('casting_time', ''),
                    'range': data.get('range', ''),
                    'components': data.get('components', []),
                    'duration': data.get('duration', ''),
                    'description': data.get('desc', [''])[0],
                    'found': True,
                }
            else:
                result = {'name': spell_name, 'found': False}

        except Exception:
            result = {'name': spell_name, 'found': False}

        self.cache[cache_key] = result
        return result


class ScenarioAnalyzer:
    """Главный анализатор сценариев"""

    def __init__(self):
        self.text_analyzer = TextAnalyzer()
        self.combat_analyzer = CombatBalanceAnalyzer()
        self.puzzle_analyzer = PuzzleAnalyzer()
        self.narrative_analyzer = NarrativeAnalyzer()
        self.dnd_api = DnDAPI()

    def full_analysis(self, scenario_text: str, party_level: int = 3,
                      party_size: int = 4) -> dict:
        """
        Полный анализ сценария.

        Args:
            scenario_text: Текст сценария
            party_level: Уровень группы
            party_size: Количество игроков

        Returns:
            Полные результаты анализа
        """
        start_time = time.time()

        # 1. Извлечение элементов
        elements = self.text_analyzer.extract_elements(scenario_text)

        # 2. Анализ боевых встреч
        monsters = self.combat_analyzer.extract_monsters_from_text(scenario_text)
        combat_analysis = self.combat_analyzer.calculate_encounter_difficulty(
            monsters, party_level, party_size
        ) if monsters else {'difficulty': 'Нет боев', 'balance_score': 0.5}

        # 3. Анализ загадок
        puzzles = elements.get('puzzle', [])
        puzzle_analysis = {}
        if puzzles:
            puzzle_text = ' '.join([p['text'] for p in puzzles])
            puzzle_analysis = self.puzzle_analyzer.analyze_puzzle_complexity(puzzle_text)
        else:
            puzzle_analysis = {'complexity_score': 0, 'level': 'Нет загадок'}

        # 4. Анализ повествования
        narrative_analysis = self.narrative_analyzer.analyze_narrative_flow(scenario_text)

        # 5. Общая оценка
        overall_score = self._calculate_overall_score(
            combat_analysis.get('balance_score', 0.5),
            puzzle_analysis.get('complexity_score', 0.5),
            narrative_analysis.get('narrative_score', 0.5)
        )

        # 6. Рекомендации
        recommendations = self._generate_overall_recommendations(
            elements, combat_analysis, puzzle_analysis, narrative_analysis
        )

        execution_time = time.time() - start_time

        return {
            'overall_score': round(overall_score, 3),
            'execution_time': round(execution_time, 2),
            'element_counts': {k: len(v) for k, v in elements.items()},
            'combat_analysis': combat_analysis,
            'puzzle_analysis': puzzle_analysis,
            'narrative_analysis': narrative_analysis,
            'text_metrics': self.text_analyzer.calculate_text_metrics(scenario_text),
            'recommendations': recommendations,
            'missing_elements': self._identify_missing_elements(elements),
        }

    def _calculate_overall_score(self, combat_score: float,
                                 puzzle_score: float, narrative_score: float) -> float:
        """Рассчитывает общий балл сценария"""
        # Взвешенная сумма (можно настроить веса)
        return (
                combat_score * 0.4 +  # Боевой баланс важен
                puzzle_score * 0.3 +  # Загадки добавляют глубину
                narrative_score * 0.3  # Повествование держит интерес
        )

    def _identify_missing_elements(self, elements: dict) -> list:
        """Определяет недостающие элементы"""
        missing = []

        required_elements = ['npc', 'location', 'encounter']

        for element in required_elements:
            if element not in elements or len(elements[element]) == 0:
                missing.append({
                    'element': element,
                    'name': self._get_element_name(element),
                    'importance': 'high' if element in ['npc', 'encounter'] else 'medium',
                })

        # Проверка специальных случаев
        if 'item' in elements and len(elements['item']) > 0:
            # Если есть предметы, но нет торговца
            has_merchant = any('торговец' in e['name'].lower() or
                               'merchant' in e['name'].lower()
                               for e in elements.get('npc', []))

            if not has_merchant:
                missing.append({
                    'element': 'npc',
                    'name': 'Торговец/Продавец',
                    'importance': 'medium',
                    'reason': 'Для продажи/покупки предметов',
                })

        return missing

    def _get_element_name(self, element_type: str) -> str:
        """Возвращает читаемое название элемента"""
        names = {
            'npc': 'Неигровые персонажи',
            'location': 'Локации',
            'encounter': 'Боевые встречи',
            'item': 'Предметы',
            'puzzle': 'Загадки',
            'trap': 'Ловушки',
            'treasure': 'Сокровища',
        }
        return names.get(element_type, element_type)

    def _generate_overall_recommendations(self, elements: dict,
                                          combat_analysis: dict,
                                          puzzle_analysis: dict,
                                          narrative_analysis: dict) -> list:
        """Генерирует общие рекомендации"""
        recommendations = []

        # Рекомендации по элементам
        if 'npc' not in elements or len(elements['npc']) < 2:
            recommendations.append("Добавьте больше NPC для социальных взаимодействий")

        if 'location' not in elements or len(elements['location']) < 2:
            recommendations.append("Добавьте разнообразные локации для исследования")

        # Рекомендации по боям
        combat_difficulty = combat_analysis.get('difficulty', '')
        if combat_difficulty in ['Легкая', 'Средняя']:
            recommendations.append("Можно усилить боевые встречи для большего вызова")
        elif combat_difficulty in ['Опасная', 'Смертельная']:
            recommendations.append("Боевые встречи могут быть слишком сложными")

        # Рекомендации по загадкам
        puzzle_score = puzzle_analysis.get('complexity_score', 0)
        if puzzle_score < 0.3:
            recommendations.append("Загадки слишком простые - усложните их")
        elif puzzle_score > 0.7:
            recommendations.append("Загадки могут быть слишком сложными - добавьте подсказки")

        # Рекомендации по повествованию
        narrative_score = narrative_analysis.get('narrative_score', 0.5)
        if narrative_score < 0.4:
            recommendations.append("Улучшите связность повествования")

        # Проверка разнообразия
        element_counts = {k: len(v) for k, v in elements.items()}
        if len(element_counts) < 4:
            recommendations.append("Добавьте больше типов контента (предметы, ловушки, сокровища)")

        return recommendations

    def analyze_specific_section(self, text: str, section_type: str) -> dict:
        """
        Анализ конкретного раздела сценария.

        Args:
            text: Текст раздела
            section_type: Тип раздела (combat, puzzle, dialogue, description)

        Returns:
            Результаты анализа раздела
        """
        if section_type == 'combat':
            monsters = self.combat_analyzer.extract_monsters_from_text(text)
            return {
                'type': 'combat',
                'monster_count': len(monsters),
                'monsters': monsters,
                'analysis': self.combat_analyzer.calculate_encounter_difficulty(
                    monsters, 5, 4
                ) if monsters else {},
            }

        elif section_type == 'puzzle':
            return {
                'type': 'puzzle',
                'analysis': self.puzzle_analyzer.analyze_puzzle_complexity(text),
            }

        elif section_type == 'dialogue':
            return {
                'type': 'dialogue',
                'line_count': text.count('\n') + 1,
                'speaker_count': len(set(re.findall(r'(\w+):', text))),
                'avg_line_length': len(text) / max(text.count('\n') + 1, 1),
            }

        elif section_type == 'description':
            return {
                'type': 'description',
                'word_count': len(text.split()),
                'sentence_count': len(re.split(r'[.!?]+', text)),
                'descriptive_word_ratio': self._count_descriptive_words(text),
            }

        else:
            return {'type': section_type, 'error': 'Unknown section type'}

    def _count_descriptive_words(self, text: str) -> float:
        """Считает описательные слова (прилагательные, наречия)"""
        # Простая эвристика - слова, оканчивающиеся на определенные суффиксы
        descriptive_suffixes = ['ый', 'ой', 'ий', 'ая', 'яя', 'ое', 'ее',
                                'о', 'е', 'и', 'но', 'то', 'во']

        words = text.split()
        descriptive_words = 0

        for word in words:
            word_lower = word.lower()
            for suffix in descriptive_suffixes:
                if word_lower.endswith(suffix):
                    descriptive_words += 1
                    break

        return descriptive_words / len(words) if words else 0


# Экспорт основных классов
__all__ = [
    'TextAnalyzer',
    'CombatBalanceAnalyzer',
    'PuzzleAnalyzer',
    'NarrativeAnalyzer',
    'DnDAPI',
    'ScenarioAnalyzer',
]
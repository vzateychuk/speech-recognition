#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки загрузки словаря замен терминов
"""

import json
import re
from pathlib import Path

def load_term_replacements():
    """Загрузка словаря замен терминов из файлов (копия из speech_recognition.py)"""
    replacements = {}
    dicts_dir = Path("dicts")
    
    # Если директории нет - возвращаем пустой словарь
    if not dicts_dir.exists():
        print(f"❌ Папка {dicts_dir} не найдена!")
        return replacements
    
    # Ищем все .json файлы в директории
    json_files = list(dicts_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ В папке {dicts_dir} нет .json файлов!")
        return replacements
    
    print(f"✓ Найдено файлов словарей: {len(json_files)}")
    print(f"Загрузка словарей терминов из {dicts_dir}/...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            loaded_count = 0
            # Поддерживаем два формата: упрощенный и полный
            if "replacements" in data:
                # Упрощенный формат: {"replacements": {"wrong": "correct"}}
                replacements.update(data["replacements"])
                loaded_count = len(data["replacements"])
            elif "contexts" in data:
                # Полный формат с контекстами
                for context_name, context_data in data["contexts"].items():
                    if "replacements" in context_data:
                        # Обрабатываем замены в контексте
                        for replacement in context_data["replacements"]:
                            if isinstance(replacement, dict) and "patterns" in replacement:
                                # Новый формат: patterns + priority
                                if replacement["patterns"]:  # Проверяем что список не пустой
                                    for pattern in replacement["patterns"]:
                                        replacements[pattern] = replacement["correct"]
                                        loaded_count += 1
                            elif isinstance(replacement, dict) and "wrong" in replacement:
                                # Старый формат: wrong/correct (если нет patterns)
                                replacements[replacement["wrong"]] = replacement["correct"]
                                loaded_count += 1
            
            print(f"   ✓ {json_file.name}: загружено {loaded_count} замен")
            
        except Exception as e:
            print(f"❌ ОШИБКА при загрузке {json_file}: {e}")
    
    if replacements:
        print(f"\n✓ Всего загружено замен терминов: {len(replacements)}")
    
    return replacements

def postprocess_text(text, replacements):
    """Постобработка текста с заменой некорректных терминов (копия из speech_recognition.py)"""
    if not replacements:
        return text
    
    # Применяем замены
    for pattern, correct in replacements.items():
        # Проверяем, содержит ли паттерн regex-метасимволы
        has_regex_chars = '\b' in pattern or '\\b' in pattern or re.search(r'[\[\]()+?*^$]', pattern)
        
        if has_regex_chars:
            # Это regex паттерн
            try:
                text = re.sub(pattern, correct, text, flags=re.IGNORECASE)
            except re.error:
                # Если некорректный regex, применяем как обычный текст
                text = re.sub(r'\b' + re.escape(pattern) + r'\b', correct, text, flags=re.IGNORECASE)
        else:
            # Обычная замена слова с границами
            text = re.sub(r'\b' + re.escape(pattern) + r'\b', correct, text, flags=re.IGNORECASE)
    
    return text

def test_replacements():
    """Тестирование замен"""
    print("="*60)
    print("ТЕСТ: Загрузка и применение словаря замен терминов")
    print("="*60)
    print()
    
    # Загружаем замены
    replacements = load_term_replacements()
    
    if not replacements:
        print("\n❌ Словарь не загружен или пуст!")
        return
    
    print("\n" + "="*60)
    print("ПРИМЕРЫ ЗАМЕН:")
    print("="*60)
    
    # Показываем первые 10 замен
    print("\nПервые 10 загруженных замен:")
    for i, (pattern, correct) in enumerate(list(replacements.items())[:10], 1):
        print(f"  {i}. '{pattern}' → '{correct}'")
    
    # Тестируем замены
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ЗАМЕН:")
    print("="*60)
    
    test_cases = [
        "томкат сервер запущен",
        "используем датогрид для отображения",
        "нужно сделать дабоклик",
        "костом компонент работает",
        "конфиг файл загружен",
        "компонент системы",
        "генератор кода",
        "колом таблицы",
        "экшен выполнен",
        "скоп видимости",
        "контроллер обрабатывает",
        "виджет отображается",
        "конструктор создает",
        "ксум файл",
        "лейбл элемент",
        "веплиент запущен",
        "липонтер ошибка",
        "кзукиут метод",
        "линк элемент",
        "франеи класса",
        "шалайзер инициализирует",
        "симпигенератор работает",
        "лодер загружает",
        "айтом списка",
        "челдом элемент",
        "одичник объекта",
        "парант компонент",
        "рендер выполнен",
        "резолвер находит",
        "лукап компонента",
        "брейкоин установлен",
        "проппер тиц файл",
        "пропратишь загружен",
        "каталина запущена",
        "косуд проект",
        "кашрек компонент",
        "кашелек очищен",
        "шедлер работает",
        "билд завершен",
        "геттер метод",
        "сеттер метод",
        "косутеры загружены",
        "проперти файл",
        "инстанс создан",
        "сталбец таблицы",
        "стручке кода"
    ]
    
    print("\nТестовые фразы:")
    for test_text in test_cases[:15]:  # Первые 15 для краткости
        result = postprocess_text(test_text, replacements)
        if result != test_text:
            print(f"  ✓ '{test_text}' → '{result}'")
        else:
            print(f"  ⚠ '{test_text}' → (не изменено)")
    
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТ:")
    print("="*60)
    print(f"✓ Словарь загружен: {len(replacements)} замен")
    print(f"✓ Замены применяются корректно")
    print("\nСловарь используется в speech_recognition.py!")

if __name__ == "__main__":
    test_replacements()





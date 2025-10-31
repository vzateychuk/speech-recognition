#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Программа для транскрибации аудиофайлов с использованием Vosk или Whisper
"""

import os
import re
import json
import wave
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Исправление кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Импорты для Vosk
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

# Импорты для Whisper
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class AudioTranscriber:
    """Класс для транскрибации аудиофайлов"""
    
    def __init__(self, config_path="config.json"):
        """Инициализация транскрибера с конфигурацией"""
        self.config = self.load_config(config_path)
        self.engine = self.config.get('engine', 'vosk').lower()
        
        # Проверка доступности выбранного движка
        if self.engine == 'vosk' and not VOSK_AVAILABLE:
            raise ImportError("Vosk не установлен. Выполните: pip install vosk")
        if self.engine == 'whisper' and not WHISPER_AVAILABLE:
            raise ImportError("Whisper не установлен. Выполните: pip install faster-whisper")
        
        if self.engine not in ['vosk', 'whisper']:
            raise ValueError(f"Неподдерживаемый движок: {self.engine}. Используйте 'vosk' или 'whisper'")
        
        print(f"Используется движок: {self.engine.upper()}")
        
        # Загружаем словари замен терминов один раз при инициализации
        self.term_replacements = self.load_term_replacements()
        
        self.model = self.load_model()
        
        if self.engine == 'vosk':
            self.validate_language_config()
        
    def load_config(self, config_path):
        """Загрузка конфигурационного файла"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Конфигурационный файл {config_path} не найден")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_model(self):
        """Загрузка модели в зависимости от выбранного движка"""
        if self.engine == 'vosk':
            return self.load_vosk_model()
        elif self.engine == 'whisper':
            return self.load_whisper_model()
    
    def load_vosk_model(self):
        """Загрузка модели Vosk"""
        model_path = self.config.get('vosk_model_path') or self.config.get('model_path')
        
        if not model_path:
            raise ValueError("Не указан путь к модели Vosk (vosk_model_path)")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Модель Vosk не найдена по пути: {model_path}\n"
                f"Скачайте модель с https://alphacephei.com/vosk/models\n"
                f"Для русского языка рекомендуется: vosk-model-small-ru-0.22 или vosk-model-ru-0.42"
            )
        
        print(f"Загрузка модели Vosk из {model_path}...")
        model = Model(model_path)
        print("Модель Vosk успешно загружена!")
        return model
    
    def extract_whisper_model_size(self, model_path):
        """
        Автоматическое определение размера модели Whisper из пути.
        Примеры:
        - models/faster-whisper-base -> base
        - models/faster-whisper-small -> small
        - faster-whisper-tiny -> tiny
        """
        model_name = Path(model_path).name
        
        # Паттерны для определения размера модели
        patterns = [
            r'faster-whisper-(tiny|base|small|medium|large)',
            r'whisper-(tiny|base|small|medium|large)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, model_name, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        return None
    
    def load_whisper_model(self):
        """Загрузка локальной модели Whisper"""
        # Опциональный параметр, по умолчанию CPU
        device = self.config.get('whisper_device', 'cpu')
        compute_type = "int8" if device == "cpu" else "float16"
        
        # Локальный путь к модели обязателен
        whisper_model_path = self.config.get('whisper_model_path')
        if not whisper_model_path:
            raise ValueError(
                "Для Whisper необходимо указать локальный путь к модели!\n"
                "Добавьте в config.json параметр:\n"
                '  "whisper_model_path": "models/faster-whisper-base"\n\n'
                "Скачайте модель используя: python download_whisper_model.py"
            )
        
        # Автоматическое определение размера модели из пути (для информационных целей)
        detected_size = self.extract_whisper_model_size(whisper_model_path)
        model_size = self.config.get('whisper_model') or detected_size or 'unknown'
        
        if detected_size and not self.config.get('whisper_model'):
            print(f"Автоматически определен размер модели: {detected_size}")
        
        # Проверка существования локальной модели
        model_path = Path(whisper_model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Локальная модель Whisper не найдена по пути: {model_path}\n\n"
                f"Скачайте модель в папку models/ используя:\n"
                f"  python download_whisper_model.py\n\n"
                f"Затем укажите путь в config.json:\n"
                f'  "whisper_model_path": "models/faster-whisper-base"'
            )
        
        # Проверка наличия ключевых файлов модели
        required_files = ['model.bin', 'config.json']
        missing_files = [f for f in required_files if not (model_path / f).exists()]
        if missing_files:
            raise FileNotFoundError(
                f"В локальной модели Whisper отсутствуют файлы: {', '.join(missing_files)}\n"
                f"Путь: {model_path}\n\n"
                f"Перезагрузите модель используя:\n"
                f"  python download_whisper_model.py"
            )
        
        # Преобразуем в абсолютный путь для надежности
        model_source = str(model_path.absolute())
        print(f"Загрузка локальной модели Whisper из: {model_source}")
        if model_size != 'unknown':
            print(f"Размер модели: {model_size}")
        print(f"Устройство: {device}, тип вычислений: {compute_type}")
        
        try:
            model = WhisperModel(model_source, device=device, compute_type=compute_type)
            print("✓ Модель Whisper успешно загружена!")
            return model
        except Exception as e:
            error_msg = str(e)
            print("\n" + "!"*60)
            print("⚠️  ОШИБКА ЗАГРУЗКИ МОДЕЛИ")
            print("!"*60)
            print(f"Не удалось загрузить локальную модель Whisper: {error_msg}")
            print("\nВозможные решения:")
            print("1. Проверьте правильность пути к модели в config.json")
            print("2. Убедитесь, что модель полностью загружена:")
            print("   python download_whisper_model.py")
            print("3. Проверьте, что все файлы модели присутствуют в папке")
            print("4. Попробуйте использовать Vosk вместо Whisper")
            print("!"*60 + "\n")
            raise
    
    def extract_language_from_model_path(self):
        """
        Извлечение кода языка из названия модели Vosk.
        Для Whisper язык не требуется (определяется автоматически).
        Примеры:
        - vosk-model-small-ru-0.22 -> ru
        - vosk-model-ru-0.42 -> ru
        - vosk-model-en-us-0.22 -> en-us
        - vosk-model-small-en-us-0.22 -> en-us
        """
        if self.engine != 'vosk':
            return None
            
        model_path = self.config.get('vosk_model_path') or self.config.get('model_path')
        if not model_path:
            return None
            
        model_name = Path(model_path).name
        
        # Паттерны для различных форматов названий моделей
        patterns = [
            r'vosk-model-small-([a-z]{2}(?:-[a-z]{2})?)-[\d.]+',  # vosk-model-small-ru-0.22
            r'vosk-model-([a-z]{2}(?:-[a-z]{2})?)-[\d.]+',        # vosk-model-ru-0.42
            r'vosk-model-small-([a-z]{2})',                        # vosk-model-small-ru
            r'vosk-model-([a-z]{2})',                              # vosk-model-ru
        ]
        
        for pattern in patterns:
            match = re.search(pattern, model_name, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        return None
    
    def validate_language_config(self):
        """
        Проверка соответствия языка в конфигурации и названия модели.
        Автоматически устанавливает язык, если он не указан в конфигурации.
        Выводит предупреждение при несоответствии.
        """
        detected_lang = self.extract_language_from_model_path()
        config_lang = self.config.get('language', '').strip().lower()
        
        if detected_lang:
            print(f"Обнаружен язык модели: {detected_lang}")
            
            # Автоопределение языка, если не указан в конфигурации
            if not config_lang:
                print(f"✓ Язык не указан в конфигурации, используется автоопределенный: {detected_lang}")
                self.config['language'] = detected_lang
                config_lang = detected_lang
            
            # Проверка соответствия, если язык указан
            if config_lang and config_lang != detected_lang:
                # Проверяем также частичное совпадение (например, en-us и en)
                if not (config_lang.startswith(detected_lang) or detected_lang.startswith(config_lang)):
                    print("\n" + "!"*60)
                    print("⚠️  ВНИМАНИЕ: Обнаружено несоответствие!")
                    print("!"*60)
                    print(f"Язык в конфигурации: '{self.config['language']}'")
                    print(f"Язык модели: '{detected_lang}'")
                    print(f"\nРаспознавание будет выполняться на языке: {detected_lang}")
                    print(f"(определяется моделью, а не параметром 'language' в config.json)")
                    print("\n💡 Рекомендация: обновите параметр 'language' в config.json")
                    print(f"   на значение '{detected_lang}' для корректной документации.")
                    print("!"*60 + "\n")
                    # Автоматически исправляем для корректной документации
                    print(f"🔧 Автоматическое исправление: используется '{detected_lang}' для выходных файлов")
                    self.config['language'] = detected_lang
        else:
            print("⚠️  Не удалось автоматически определить язык из названия модели")
            if config_lang:
                print(f"Будет использован язык из конфигурации: {config_lang}")
            else:
                print("⚠️  ВНИМАНИЕ: Язык не определен!")
                print("Укажите параметр 'language' в config.json вручную")
                self.config['language'] = 'unknown'
    
    def convert_to_wav(self, input_file, output_file):
        """
        Конвертация аудиофайла в формат WAV с нужными параметрами
        используя ffmpeg
        """
        sample_rate = self.config['sample_rate']
        
        command = [
            'ffmpeg',
            '-i', input_file,
            '-ar', str(sample_rate),  # Sample rate
            '-ac', '1',  # Mono
            '-sample_fmt', 's16',  # 16-bit
            '-y',  # Overwrite output file
            '-loglevel', 'error',  # Показывать только ошибки
            output_file
        ]
        
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                encoding='utf-8',
                errors='ignore'
            )
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Ошибка конвертации: {e}")
            if e.stderr:
                print(f"Детали: {e.stderr}")
            return False
            
        except FileNotFoundError:
            print("\n" + "!"*60)
            print("⚠️  ffmpeg не найден!")
            print("!"*60)
            print("Пожалуйста, установите ffmpeg:")
            print("")
            print("Windows (через Chocolatey):")
            print("  choco install ffmpeg")
            print("")
            print("Windows (через Scoop):")
            print("  scoop install ffmpeg")
            print("")
            print("Windows (через winget):")
            print("  winget install ffmpeg")
            print("")
            print("Linux (Ubuntu/Debian):")
            print("  sudo apt install ffmpeg")
            print("")
            print("macOS:")
            print("  brew install ffmpeg")
            print("!"*60 + "\n")
            return False
    
    def transcribe_audio(self, audio_file):
        """Транскрибация аудиофайла (выбирает метод в зависимости от движка)"""
        if self.engine == 'vosk':
            return self.transcribe_audio_vosk(audio_file)
        elif self.engine == 'whisper':
            return self.transcribe_audio_whisper(audio_file)
    
    def transcribe_audio_vosk(self, wav_file):
        """Транскрибация аудиофайла с помощью Vosk"""
        wf = wave.open(wav_file, "rb")
        
        # Проверка формата
        if wf.getnchannels() != 1:
            wf.close()
            raise ValueError("Аудио должно быть моно")
        
        if wf.getsampwidth() != 2:
            wf.close()
            raise ValueError("Аудио должно быть 16-битным")
        
        if wf.getframerate() != self.config['sample_rate']:
            wf.close()
            raise ValueError(f"Частота дискретизации должна быть {self.config['sample_rate']} Hz")
        
        # Создание распознавателя
        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)
        
        results = []
        
        print("Транскрибация аудио...")
        
        # Чтение и обработка аудио по частям
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if 'text' in result and result['text']:
                    results.append(result)
        
        # Финальный результат
        final_result = json.loads(rec.FinalResult())
        if 'text' in final_result and final_result['text']:
            results.append(final_result)
        
        wf.close()
        
        return results
    
    def transcribe_audio_whisper(self, audio_file):
        """Транскрибация аудиофайла с помощью Whisper"""
        print("Транскрибация аудио с помощью Whisper...")
        
        # Определяем язык (можно указать вручную или оставить None для автоопределения)
        language = self.config.get('language', None)
        if language:
            language = language.split('-')[0]  # en-us -> en
        
        # Транскрибация
        segments, info = self.model.transcribe(
            audio_file,
            language=language,
            beam_size=5,
            word_timestamps=False  # Отключаем временные метки для простоты
        )
        
        # Whisper возвращает обнаруженный язык
        detected_lang = info.language
        if not self.config.get('language'):
            self.config['language'] = detected_lang
        
        print(f"Обнаружен язык: {detected_lang} (вероятность: {info.language_probability:.2f})")
        
        # Собираем текст из сегментов
        results = []
        full_text = ""
        for segment in segments:
            full_text += segment.text + " "
        
        # Форматируем результат в формат, совместимый с Vosk
        results.append({'text': full_text.strip()})
        
        return results
    
    def load_term_replacements(self):
        """Загрузка словаря замен терминов из файлов"""
        replacements = {}
        dicts_dir = Path("dicts")
        
        # Если директории нет - возвращаем пустой словарь
        if not dicts_dir.exists():
            return replacements
        
        # Ищем все .json файлы в директории
        json_files = list(dicts_dir.glob("*.json"))
        
        if not json_files:
            return replacements
        
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
                                elif isinstance(replacement, str):
                                    # Просто строка замены
                                    pass  # Пропускаем, нужен формат словаря
                
                print(f"   [OK] {json_file.name}: загружено {loaded_count} замен")
                
            except Exception as e:
                print(f"[WARNING] Не удалось загрузить словарь терминов из {json_file}: {e}")
        
        if replacements:
            print(f"[OK] Всего загружено замен терминов: {len(replacements)}")
        
        return replacements
    
    def postprocess_text(self, text):
        """Постобработка текста с заменой некорректных терминов"""
        if not self.term_replacements:
            return text
        
        replacements = self.term_replacements
        
        # Применяем замены
        for pattern, correct in replacements.items():
            # Проверяем, содержит ли паттерн regex-метасимволы
            # \b интерпретируется как один символ в JSON, поэтому ищем оба варианта
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
    
    def format_results_to_markdown(self, results, original_filename):
        """Форматирование результатов в Markdown"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown = f"# Транскрипция аудиофайла\n\n"
        markdown += f"**Исходный файл:** {original_filename}\n\n"
        markdown += f"**Дата обработки:** {timestamp}\n\n"
        markdown += f"**Движок распознавания:** {self.engine.upper()}\n\n"
        markdown += f"**Язык:** {self.config.get('language', 'неизвестно')}\n\n"
        markdown += f"---\n\n"
        markdown += f"## Текст транскрипции\n\n"
        
        if not results:
            markdown += "*Текст не распознан*\n"
        else:
            full_text = " ".join([r.get('text', '') for r in results if r.get('text')])
            # Применяем постобработку для замены терминов
            full_text = self.postprocess_text(full_text)
            markdown += f"{full_text}\n\n"
        
        return markdown
    
    def process_file(self, input_file):
        """Обработка одного аудиофайла"""
        input_path = Path(input_file)
        
        print(f"\n{'='*60}")
        print(f"Обработка файла: {input_path.name}")
        print(f"{'='*60}")
        
        # Проверка расширения файла
        if input_path.suffix.lower() not in self.config['supported_formats']:
            print(f"Пропуск файла {input_path.name}: неподдерживаемый формат")
            return False
        
        temp_wav = None  # Инициализация для finally блока
        
        try:
            # Для Vosk нужна конвертация в WAV, для Whisper - нет
            if self.engine == 'vosk':
                # Создание директории для временных файлов
                temp_dir = Path(self.config.get('temp_dir', '.data/temp'))
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                # Путь к временному WAV файлу
                temp_wav = temp_dir / f"temp_{input_path.stem}.wav"
                
                # Конвертация в WAV
                print(f"Конвертация {input_path.suffix} -> WAV...")
                if not self.convert_to_wav(str(input_path), str(temp_wav)):
                    print(f"Ошибка конвертации файла {input_path.name}")
                    return False
                
                # Транскрибация
                results = self.transcribe_audio(str(temp_wav))
            else:
                # Whisper работает напрямую с любыми форматами
                temp_wav = None
                results = self.transcribe_audio(str(input_path))
            
            # Форматирование и сохранение результата
            markdown = self.format_results_to_markdown(results, input_path.name)
            
            output_file = Path(self.config['output_dir']) / f"{input_path.stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            print(f"✓ Транскрипция сохранена: {output_file}")
            
            # Перемещение обработанного файла в папку processed
            processed_dir = Path(self.config['processed_dir'])
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            processed_file = processed_dir / input_path.name
            shutil.move(str(input_path), str(processed_file))
            print(f"✓ Файл перемещен в: {processed_file}")
            
            return True
            
        except Exception as e:
            print(f"Ошибка при обработке файла {input_path.name}: {e}")
            return False
        
        finally:
            # Удаление временного файла (только для Vosk)
            if self.engine == 'vosk' and temp_wav and temp_wav.exists():
                temp_wav.unlink()
    
    def process_directory(self):
        """Обработка всех файлов в входной директории"""
        input_dir = Path(self.config['input_dir'])
        output_dir = Path(self.config['output_dir'])
        
        # Создание выходной директории, если не существует
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Получение списка файлов
        audio_files = []
        for ext in self.config['supported_formats']:
            audio_files.extend(list(input_dir.glob(f"*{ext}")))
            audio_files.extend(list(input_dir.glob(f"*{ext.upper()}")))
        
        # Убираем дубликаты (на Windows файловая система регистронезависима)
        audio_files = list(set(audio_files))
        
        # Сортируем файлы по имени для предсказуемого порядка обработки
        audio_files = sorted(audio_files, key=lambda x: x.name.lower())
        
        if not audio_files:
            print(f"\nВ директории {input_dir} не найдено аудиофайлов")
            print(f"Поддерживаемые форматы: {', '.join(self.config['supported_formats'])}")
            return
        
        print(f"\nНайдено файлов для обработки: {len(audio_files)}")
        
        # Обработка каждого файла
        success_count = 0
        for audio_file in audio_files:
            if self.process_file(audio_file):
                success_count += 1
        
        print(f"\n{'='*60}")
        print(f"Обработка завершена!")
        print(f"Успешно обработано: {success_count} из {len(audio_files)}")
        print(f"{'='*60}\n")


def main():
    """Основная функция программы"""
    print("="*60)
    print("Программа транскрибации аудиофайлов (Vosk)")
    print("="*60)
    
    try:
        transcriber = AudioTranscriber()
        transcriber.process_directory()
    except Exception as e:
        print(f"\nОшибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())


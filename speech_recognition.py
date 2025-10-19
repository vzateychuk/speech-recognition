#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Программа для транскрибации аудиофайлов с использованием библиотеки Vosk
"""

import os
import re
import json
import wave
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from vosk import Model, KaldiRecognizer


class AudioTranscriber:
    """Класс для транскрибации аудиофайлов"""
    
    def __init__(self, config_path="config.json"):
        """Инициализация транскрибера с конфигурацией"""
        self.config = self.load_config(config_path)
        self.model = self.load_model()
        self.validate_language_config()
        
    def load_config(self, config_path):
        """Загрузка конфигурационного файла"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Конфигурационный файл {config_path} не найден")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_model(self):
        """Загрузка модели Vosk"""
        model_path = self.config['model_path']
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Модель не найдена по пути: {model_path}\n"
                f"Скачайте модель с https://alphacephei.com/vosk/models\n"
                f"Для русского языка рекомендуется: vosk-model-small-ru-0.22 или vosk-model-ru-0.42"
            )
        
        print(f"Загрузка модели из {model_path}...")
        model = Model(model_path)
        print("Модель успешно загружена!")
        return model
    
    def extract_language_from_model_path(self):
        """
        Извлечение кода языка из названия модели.
        Примеры:
        - vosk-model-small-ru-0.22 -> ru
        - vosk-model-ru-0.42 -> ru
        - vosk-model-en-us-0.22 -> en-us
        - vosk-model-small-en-us-0.22 -> en-us
        """
        model_path = self.config['model_path']
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
    
    def transcribe_audio(self, wav_file):
        """Транскрибация аудиофайла"""
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
    
    def format_results_to_markdown(self, results, original_filename):
        """Форматирование результатов в Markdown"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown = f"# Транскрипция аудиофайла\n\n"
        markdown += f"**Исходный файл:** {original_filename}\n\n"
        markdown += f"**Дата обработки:** {timestamp}\n\n"
        markdown += f"**Язык:** {self.config['language']}\n\n"
        markdown += f"---\n\n"
        markdown += f"## Текст транскрипции\n\n"
        
        if not results:
            markdown += "*Текст не распознан*\n"
        else:
            full_text = " ".join([r.get('text', '') for r in results if r.get('text')])
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
        
        # Путь к временному WAV файлу
        temp_wav = Path(self.config['output_dir']) / f"temp_{input_path.stem}.wav"
        
        try:
            # Конвертация в WAV
            print(f"Конвертация {input_path.suffix} -> WAV...")
            if not self.convert_to_wav(str(input_path), str(temp_wav)):
                print(f"Ошибка конвертации файла {input_path.name}")
                return False
            
            # Транскрибация
            results = self.transcribe_audio(str(temp_wav))
            
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
            # Удаление временного файла
            if temp_wav.exists():
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


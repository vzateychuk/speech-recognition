#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
<<<<<<< Updated upstream
Скрипт для загрузки модели Whisper в локальную папку models/
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("Ошибка: huggingface_hub не установлен")
    print("Установите его командой: pip install huggingface_hub")
    sys.exit(1)

def download_whisper_model(model_size="base", output_dir="models"):
    """
    Загрузка модели Whisper из Hugging Face Hub в локальную папку
=======
Скрипт для загрузки моделей Whisper в локальную папку models/
"""

import sys
import os
from pathlib import Path

def download_whisper_model(model_size="base", output_dir="models"):
    """
    Загружает модель Whisper в локальную папку
>>>>>>> Stashed changes
    
    Args:
        model_size: размер модели (tiny, base, small, medium, large)
        output_dir: директория для сохранения модели
    """
<<<<<<< Updated upstream
    # Репозиторий модели на Hugging Face
    repo_id = f"Systran/faster-whisper-{model_size}"
    
    # Путь для сохранения
    model_dir = Path(output_dir) / f"faster-whisper-{model_size}"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"="*60)
    print(f"Загрузка модели Whisper ({model_size})")
    print(f"="*60)
    print(f"Репозиторий: {repo_id}")
    print(f"Директория назначения: {model_dir}")
    print(f"\nРазмеры моделей:")
    print(f"  - tiny:   ~75 MB")
    print(f"  - base:   ~140 MB  (рекомендуется)")
    print(f"  - small:  ~460 MB")
    print(f"  - medium: ~1.5 GB")
    print(f"  - large:  ~3 GB")
    print(f"\nНачинаю загрузку...")
    print(f"="*60)
    
    try:
        # Загрузка модели
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(model_dir),
            local_dir_use_symlinks=False  # Не использовать симлинки на Windows
        )
        
        print(f"\n✓ Модель успешно загружена!")
        print(f"✓ Путь к модели: {model_dir}")
        print(f"\nТеперь укажите в config.json:")
        print(f'  "whisper_model_path": "models/faster-whisper-{model_size}"')
        print(f"="*60)
        
        return str(model_dir)
        
    except Exception as e:
        print(f"\n✗ Ошибка при загрузке модели: {e}")
        print(f"\nПроверьте:")
        print(f"1. Интернет-соединение")
        print(f"2. Доступ к https://huggingface.co")
        print(f"3. Если используете прокси, настройте переменные окружения HTTP_PROXY/HTTPS_PROXY")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Загрузка модели Whisper в локальную папку")
    parser.add_argument(
        "--model-size",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Размер модели (по умолчанию: base)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="Директория для сохранения модели (по умолчанию: models)"
=======
    output_path = Path(output_dir) / f"faster-whisper-{model_size}"
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print(f"Загрузка модели Whisper: {model_size}")
    print("="*60)
    print(f"Директория: {output_path.absolute()}")
    print("\nЭто может занять некоторое время в зависимости от размера модели...")
    print(f"Размеры моделей:")
    print("  - tiny:   ~75 MB")
    print("  - base:   ~140 MB")
    print("  - small:  ~460 MB")
    print("  - medium: ~1.5 GB")
    print("  - large:  ~3 GB")
    print()
    
    # Пробуем использовать faster-whisper (предпочтительно)
    try:
        from faster_whisper import WhisperModel
        print("Используется faster-whisper...")
        
        # Загружаем модель в указанную директорию
        print(f"Загрузка модели {model_size}...")
        model = WhisperModel(model_size, device="cpu", download_root=str(output_path))
        
        # Проверяем что файлы модели действительно загружены
        model_bin = output_path / "model.bin"
        config_file = output_path / "config.json"
        
        if model_bin.exists() or config_file.exists():
            print(f"\n✓ Модель {model_size} успешно загружена!")
            print(f"  Путь: {output_path.absolute()}")
            return True
        else:
            # Модель могла загрузиться в кеш Hugging Face
            # Проверяем стандартное местоположение кеша
            import os
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            print(f"\n⚠ Модель могла загрузиться в кеш Hugging Face")
            print(f"Проверяем: {cache_dir}")
            print(f"\n✓ Модель {model_size} готова к использованию!")
            print(f"Укажите в config.json путь к модели:")
            print(f'  "whisper_model_path": "models/faster-whisper-{model_size}"')
            print(f"\nПримечание: faster-whisper может использовать кеш Hugging Face")
            print(f"Для принудительной загрузки в локальную папку используйте huggingface_hub")
            return True
        
    except ImportError:
        # Пробуем использовать huggingface_hub для прямой загрузки
        try:
            from huggingface_hub import snapshot_download
            print("Используется huggingface_hub для прямой загрузки...")
            
            model_id = f"guillaumekln/faster-whisper-{model_size}"
            print(f"Загрузка модели: {model_id}")
            print(f"В директорию: {output_path.absolute()}")
            
            snapshot_download(
                repo_id=model_id,
                local_dir=str(output_path),
                local_dir_use_symlinks=False
            )
            
            print(f"\n✓ Модель {model_size} успешно загружена!")
            print(f"  Путь: {output_path.absolute()}")
            return True
            
        except ImportError:
            print("="*60)
            print("ОШИБКА: Не установлены необходимые библиотеки!")
            print("="*60)
            print("\nУстановите одну из библиотек:")
            print("  1. faster-whisper (рекомендуется):")
            print("     pip install faster-whisper")
            print("\n  2. ИЛИ huggingface_hub (для прямой загрузки):")
            print("     pip install huggingface_hub")
            print("\nРекомендуется установить faster-whisper:")
            print("  pip install faster-whisper")
            sys.exit(1)
        
    except Exception as e:
        print("\n" + "!"*60)
        print(f"ОШИБКА при загрузке модели {model_size}")
        print("!"*60)
        print(f"Детали: {e}")
        print("\nВозможные решения:")
        print("1. Проверьте подключение к интернету")
        print("2. Установите faster-whisper: pip install faster-whisper")
        print("3. ИЛИ установите huggingface_hub: pip install huggingface_hub")
        print("4. Попробуйте другую модель (например, tiny вместо base)")
        print("5. Проверьте свободное место на диске")
        print("!"*60)
        return False


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Загрузка моделей Whisper в локальную папку models/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python download_whisper_model.py base        # Загрузить модель base
  python download_whisper_model.py tiny        # Загрузить модель tiny
  python download_whisper_model.py --all       # Загрузить все модели (tiny, base)
        """
    )
    
    parser.add_argument(
        'model_size',
        nargs='?',
        default='base',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Размер модели для загрузки (по умолчанию: base)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Загрузить все рекомендуемые модели (tiny, base)'
    )
    
    parser.add_argument(
        '--output',
        default='models',
        help='Директория для сохранения моделей (по умолчанию: models)'
>>>>>>> Stashed changes
    )
    
    args = parser.parse_args()
    
<<<<<<< Updated upstream
    download_whisper_model(args.model_size, args.output_dir)

=======
    if args.all:
        print("Загрузка всех рекомендуемых моделей...\n")
        models_to_download = ['tiny', 'base']
        success_count = 0
        for model in models_to_download:
            print(f"\n{'='*60}")
            print(f"Загрузка модели: {model}")
            print(f"{'='*60}\n")
            if download_whisper_model(model, args.output):
                success_count += 1
            print()
        
        print(f"\n{'='*60}")
        print(f"Загружено моделей: {success_count}/{len(models_to_download)}")
        print(f"{'='*60}\n")
        
        if success_count == len(models_to_download):
            print("✓ Все модели успешно загружены!")
            print(f"\nИспользуйте в config.json:")
            print('  "whisper_model_path": "models/faster-whisper-tiny"  # или base')
        else:
            print("⚠ Некоторые модели не удалось загрузить.")
            sys.exit(1)
    else:
        success = download_whisper_model(args.model_size, args.output)
        if success:
            print(f"\n✓ Модель {args.model_size} успешно загружена!")
            print(f"Используйте в config.json:")
            print(f'  "whisper_model_path": "models/faster-whisper-{args.model_size}"')
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
>>>>>>> Stashed changes

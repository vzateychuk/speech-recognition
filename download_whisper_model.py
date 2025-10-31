#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
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
    
    Args:
        model_size: размер модели (tiny, base, small, medium, large)
        output_dir: директория для сохранения модели
    """
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
    )
    
    args = parser.parse_args()
    
    download_whisper_model(args.model_size, args.output_dir)


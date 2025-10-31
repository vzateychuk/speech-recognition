# Быстрый старт

## 🚀 Попробуйте оба движка!

### Шаг 1: Установка

```powershell
pip install -r requirements.txt
```

### Шаг 2: Попробуйте Whisper (проще всего)

Отредактируйте `config.json`:
```json
{
  "engine": "whisper",
  "whisper_model": "base",
  "whisper_device": "cpu",
  "input_dir": ".data/input",
  "output_dir": ".data/output",
  "processed_dir": ".data/processed",
  "sample_rate": 16000,
  "supported_formats": [".wav", ".mp3", ".ogg", ".flac", ".m4a", ".wma", ".aac"]
}
```

Положите аудиофайл в `.data/input/` и запустите:
```powershell
python speech_recognition.py
```

**Готово!** При первом запуске модель скачается автоматически.

### Шаг 3: Сравните с Vosk

1. Установите ffmpeg:
   ```powershell
   winget install ffmpeg
   ```

2. Скачайте модель Vosk: https://alphacephei.com/vosk/models

3. Измените `config.json`:
   ```json
   {
     "engine": "vosk",
     "vosk_model_path": "models/vosk-model-small-ru-0.22",
     ...
   }
   ```

4. Запустите снова:
   ```powershell
   python speech_recognition.py
   ```

### 💡 Сравнение результатов

Оба результата сохраняются в `.data/output/`:
- В файле `.md` указан использованный движок
- Сравните качество и скорость!

## 📊 Какой движок выбрать?

- **Whisper** - для максимального качества (рекомендуется)
- **Vosk** - для максимальной скорости

**Попробуйте оба и решите сами!** 🎯








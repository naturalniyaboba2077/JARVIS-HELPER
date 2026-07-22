# Jarvis Voice Assistant

Локальный голосовой помощник для Windows с русской локализацией.

## Возможности

- Wake-word «Джарвис» / `Jarvis` с фонетическим и fuzzy-распознаванием.
- Локальный STT через faster-whisper (`small`) с откатом на Google Speech.
- Local-first LLM: Ollama для простых запросов, DeepSeek через OpenRouter для сложных.
- TTS `auto`: локальный Piper при наличии модели, иначе edge-tts; доступны ручные режимы.
- Локальные быстрые команды без обращения к LLM.
- Действия через теги: приложения, музыка, терминал, Python, календарь, память и Obsidian.
- Anti-wipe защита при выполнении кода: блокируется снос Windows, дисков, проекта и vault.
- Нативное окно pywebview и отдельный экранный voice-overlay.
- Панель настроек, самодиагностика и универсальное открытие установленных приложений.

## Запуск

Обычный запуск — ярлык `J.A.R.V.I.S..lnk` на рабочем столе. Он вызывает
`pythonw.exe jarvis.py` без консольного окна. Создать ярлык заново:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_shortcut.ps1
```

Для диагностики с видимой консолью:

```powershell
.\launch_jarvis.bat
```

Настройки и API-ключ хранятся в gitignored-файле `jarvis_config.json`.
Шаблон: `jarvis_config.example.json`. Переменные окружения имеют приоритет.

## Проверка

Используй Python 3.10, которым запускается приложение:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" test_regression.py
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" test_jarvis_functions.py
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" test_safety.py
```

Команда «статус Джарвиса» проверяет LLM, STT, TTS, память и каталог программ.
Проверка окружения без запуска микрофона: `python health_check.py`.

# J.A.R.V.I.S. — установка и запуск

## Runtime

Приложение сейчас запускается системным Python 3.10:

```text
%LOCALAPPDATA%\Programs\Python\Python310\python.exe
```

Устанавливай зависимости именно в него:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" -m pip install -r requirements.txt
```

Python 3.10 достигает upstream EOL 4 октября 2026 года. Переход на новую версию
нужно делать отдельным изменением с проверкой аудио, CUDA, pywebview и тестов.

## Конфигурация

Скопируй `jarvis_config.example.json` в `jarvis_config.json` и добавь ключ
OpenRouter. Реальный файл игнорируется Git. Переменные окружения имеют приоритет
над JSON, но постоянные настройки не следует помещать в `.bat`-лаунчеры.

Основные параметры:

```jsonc
{
  "OPENROUTER_API_KEY": "sk-or-v1-...",
  "JARVIS_LLM": "local",
  "OLLAMA_MODEL": "qwen2.5:3b",
  "JARVIS_LLM_DEADLINE": "1.5",
  "STT_ENGINE": "whisper",
  "WHISPER_MODEL": "small",
  "JARVIS_PAUSE_THRESHOLD": "2.6",
  "JARVIS_WAKE_COMMAND_WINDOW": "10.0",
  "JARVIS_PHRASE_TIME_LIMIT": "45.0",
  "TTS_ENGINE": "auto",
  "PIPER_VOICE": "dmitri",
  "JARVIS_FOLLOWUP_MODE": "strict",
  "JARVIS_UI": "on",
  "JARVIS_OVERLAY": "on"
}
```

- `STT_ENGINE=whisper` — локальный faster-whisper; при ошибке используется Google.
- `WHISPER_MODEL=small` — текущий обязательный default для надёжного wake-word.
- `TTS_ENGINE=auto` — Piper при наличии модели, иначе Microsoft edge-tts.
- `TTS_ENGINE=edge` — принудительно Microsoft DmitryNeural.
- `TTS_ENGINE=piper` — локальная модель из `piper_models/`.
- `TTS_ENGINE=xtts` — тяжёлое опциональное клонирование голоса.

Настройки можно менять через кнопку ⚙ в окне. Они сохраняются в
`jarvis_config.json` и применяются после перезапуска.

## Ollama

Установи Ollama и загрузить локальную модель:

```powershell
ollama pull qwen2.5:3b
```

Jarvis проверяет сервер, при необходимости запускает `ollama serve`, прогревает
модель и использует облачный DeepSeek как fallback.

## Запуск

Обычный запуск с видимой консолью и логами:

```powershell
python jarvis.py
```

Подробные события пишутся в `logs/jarvis_YYYY-MM-DD.log`.

Ярлык на рабочем столе без консольного окна (`pythonw.exe jarvis.py`):

```powershell
powershell -ExecutionPolicy Bypass -File .\install_shortcut.ps1
```

## Голос и микрофон

- Для выбора микрофона задай `JARVIS_MIC_INDEX` по номеру из стартового списка.
- Порог конца фразы задаётся `JARVIS_PAUSE_THRESHOLD`; default `2.6` допускает
  естественную паузу во время длинного вопроса.
- Отдельное обращение «Джарвис» открывает тихое 10-секундное окно: ассистент не
  произносит «Слушаю» поверх начала следующей фразы.
- `JARVIS_PHRASE_TIME_LIMIT=45` позволяет диктовать длинные вопросы и код.
- После ответа действует 15-секундное окно продолжения диалога без wake-word.
- Piper-голос выбирается через `PIPER_VOICE`: `dmitri`, `ruslan`, `denis`, `irina`.

## Безопасность исполнения

Политика — anti-wipe only. `[EXECUTE_PYTHON]` и `[CMD:]` блокируют снос дисков,
Windows, системного реестра, репозитория и Obsidian vault. Голосового подтверждения
нет. Обычная автоматизация и операции вне защищённых корней выполняются сразу.

## Проверка после изменений

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" test_regression.py
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" test_jarvis_functions.py
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" test_safety.py
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" health_check.py
```

Не перезапускай фоновый listener внутри командного цикла и не убирай worker-thread
из LLM deadline/failover — эти решения защищены регрессионными тестами.

## Telegram — личный аккаунт

Jarvis использует официальный MTProto-клиент Telethon. Данные `Telegram Desktop/tdata`
напрямую не читаются и не копируются.

1. Открой `https://my.telegram.org/apps` и создай приложение для своего аккаунта.
2. В панели настроек Jarvis укажи `API ID`, `API Hash` и телефон в формате `+79991234567`.
3. Нажми «получить код», введи код из Telegram и нажми «подключить».
4. Если включена двухэтапная аутентификация, введи пароль 2FA. Он не сохраняется.

Сессия хранится локально в `telegram_data/` и исключена из Git. Экспорт диалогов
записывается в `Documents/Jarvis Telegram Exports/` в формате Markdown.

Примеры голосовых команд:

- «Джарвис, покажи мои чаты в телеграме».
- «Джарвис, прочитай последние 10 сообщений из чата с Иваном».
- «Джарвис, выгрузи из телеграма диалог с Иваном, последние 200 сообщений».
- «Джарвис, отправь Ивану в телеграме сообщение буду через час» — отправка произойдёт только после отдельного подтверждения.

# Jarvis

Голосовой ассистент для Windows с управлением на русском. Слушает слово
«Джарвис», распознаёт речь, отвечает голосом и выполняет действия: открывает
приложения и сайты, включает музыку, выполняет команды в терминале, запускает
Python, ведёт заметки, список дел и таймеры.

## Что нужно

- Windows 10 или 11
- Python 3.10
- Микрофон
- Ключ [OpenRouter](https://openrouter.ai) для облачной модели

## Установка

```powershell
git clone https://github.com/naturalniyaboba2077/JARVIS-HELPER.git
cd JARVIS-HELPER
python -m pip install -r requirements.txt
copy jarvis_config.example.json jarvis_config.json
```

Открой `jarvis_config.json` и впиши свой ключ в `OPENROUTER_API_KEY`.
Файл с ключом в Git не попадает.

## Запуск

```powershell
python jarvis.py
```

Скажи «Джарвис», дождись «Слушаю, сэр» и дай команду.

## Быстрый старт без GPU и локальных моделей

Чтобы всё заработало сразу, только через облако, поставь в `jarvis_config.json`:

```json
"JARVIS_LLM": "cloud",
"STT_ENGINE": "google",
"TTS_ENGINE": "edge"
```

Локальные ускорения ставятся по желанию: Ollama (`ollama pull qwen2.5:3b`) для
быстрой офлайн-модели, faster-whisper на видеокарте для распознавания и Piper для
офлайн-голоса. Подробности — в [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md).

## Примеры команд

- «Джарвис, открой браузер»
- «Джарвис, зайди на youtube.com»
- «Джарвис, включи музыку»
- «Джарвис, какая погода в Москве»
- «Джарвис, поставь таймер на 10 минут»
- «Джарвис, сделай скриншот»
- «Джарвис, статус» — проверка LLM, распознавания, синтеза и памяти

## Тесты

```powershell
python test_regression.py
python test_jarvis_functions.py
python test_safety.py
```

## Структура

- `jarvis.py` — приложение целиком
- `overlay.py` — экранная визуализация голоса (отдельный процесс)
- `ui/` — окно интерфейса
- `pc_apps.txt` — каталог установленных программ для команды «открой …»
- `install_shortcut.ps1` — создаёт ярлык на рабочем столе

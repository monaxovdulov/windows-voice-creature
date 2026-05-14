# Сборка и релиз

## Локальная сборка

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python scripts\build_windows.py
```

После сборки приложение находится в:

```text
dist/screen-creature/screen-creature.exe
```

## Голосовая модель

Модель не хранится в Git, потому что она крупная. Для локальной сборки:

```powershell
.\scripts\download_vosk_model.ps1
python scripts\build_windows.py
```

Если `models/` существует во время сборки, PyInstaller добавит ее внутрь `dist/screen-creature/models`.

## GitHub Actions

Workflow `.github/workflows/windows-build.yml` запускается при push и pull request:

1. Ставит Python 3.11.
2. Устанавливает пакет с dev-зависимостями.
3. Запускает тесты.
4. Собирает Windows artifact через PyInstaller.
5. Загружает `screen-creature-windows` как artifact.

## Рекомендация для релиза

Для первого релиза лучше публиковать два артефакта:

- `screen-creature-windows.zip` с приложением.
- Отдельную ссылку/инструкцию для скачивания Vosk-модели.

Так репозиторий и CI остаются легкими, а пользователь может выбрать, нужна ли ему офлайн-речь.


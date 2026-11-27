# Сборка Windows-установщика

Сборка рассчитана на Windows x64, Python 3.12, PowerShell и Inno Setup 6.7.4. Вспомогательная программа установщика собирается компилятором C# из .NET Framework 4.x. Выполняйте команды в корне репозитория.

1. Подготовьте окружение.

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m pip install pyinstaller==6.22.3 Pillow==13.0.0
   ```

2. Скачайте `TgWsProxy_windows.exe` из [релиза tg-ws-proxy 1.12.0](https://github.com/Flowseal/tg-ws-proxy/releases/tag/v1.12.0). Установщик сверяет SHA-256 этого файла со значением в `installer/Full.iss`.

3. Укажите пути к скачанному файлу и компилятору Inno Setup.

   ```powershell
   .\installer\BuildFull.ps1 -TelegramBinary "$env:USERPROFILE\Downloads\TgWsProxy_windows.exe" -Python ".\.venv\Scripts\python.exe" -Compiler "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
   ```

Установщик появится в `release/ZapretApp-1.0-BETA-Setup-r5.exe`.

## Проверка интерфейса и компонентов

```powershell
$env:PYTHONPATH = (Resolve-Path vendor/tgws).Path
.\.venv\Scripts\python.exe -m unittest test_english_ui test_component_actions test_language_local test_autoselect_local test_updates_local
```

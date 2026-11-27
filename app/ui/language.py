"""Local UI translations. User input and log contents are not translated."""
import json
import os
import re
from pathlib import Path
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QAbstractButton, QComboBox, QLabel, QLineEdit, QSpinBox, QTabWidget, QWidget

EN = {
    'Центр связи': 'Connection center', 'Локальный прокси': 'Local proxy',
    'Discord и YouTube': 'Discord and YouTube', 'Настроить Telegram': 'Set up Telegram',
    'Быстрые действия': 'Quick actions',
    'Проверить связь': 'Check connectivity', 'Доступность сайтов': 'Website availability',
    'Ещё не проверялось': 'Not checked yet', 'Проверяем…': 'Checking…',
    'Доступен': 'Available', 'Недоступен': 'Unavailable', 'Нет ответа': 'No response',
    'Клиент подключён': 'Client connected', 'Ожидание клиента': 'Waiting for a client',
    'Прокси выключен': 'Proxy is off', 'Вернуть как было': 'Undo last change',
    'Вернуть предыдущую стратегию и версию Zapret': 'Restore the previous Zapret strategy and version',
    'Вернуть предыдущую версию. Если нужно, приложение перезапустится.':
        'Restore the previous version. The app will restart if needed.',
    'Нет предыдущих настроек': 'No previous settings', 'Настройки уже выбраны': 'Already selected',
    'Стратегия не найдена': 'Strategy not found', 'Настройки восстановлены': 'Previous settings restored',
    'Настройки Zapret применены': 'Zapret settings applied',
    'Не удалось определить настройки службы': 'Could not identify the service settings',
    'Что нового': 'What’s new', 'Загрузка описания…': 'Loading release notes…',
    'Проверка связи': 'Connectivity check',
    'На главной можно проверить Discord, YouTube и Telegram Web и увидеть, подключён ли клиент к Telegram-прокси.':
        'On Home you can check Discord, YouTube and Telegram Web and see whether a client is connected to the Telegram proxy.',
    'Отмена последнего изменения': 'Undo the last change',
    'Кнопка «Вернуть как было» возвращает предыдущую стратегию или версию Zapret. На вкладке Telegram она возвращает предыдущую версию прокси.':
        'Undo last change restores your previous Zapret strategy or version. On the Telegram tab it restores your previous proxy version.',
    'Оформление главной': 'Home screen',
    'У замка между кнопками Telegram и Zapret теперь прозрачный фон.':
        'The lock between the Telegram and Zapret buttons now has a transparent background.',
    'Открыть на GitHub': 'Open on GitHub', 'Последний релиз': 'Latest release',
    'Автор не добавил описание.': 'The author did not provide release notes.',
    'Не удалось загрузить описание.': 'Could not load release notes.',
    'На какой диск скачивать обновления?': 'Which drive should store downloaded updates?',
    'Не удалось найти доступные диски.': 'No drives were found.',
    'Продолжить': 'Continue',
    'Папка для загрузки обновлений': 'Update download folder',
    'Выбрать диск или папку…': 'Choose drive or folder…', 'Открыть папку': 'Open folder',
    'При выборе диска приложение создаст на нём папку со своим названием.':
        'Selecting a drive creates a folder named after the app on that drive.',
    'Главная': 'Home', 'Telegram': 'Telegram', 'Проверка': 'Diagnostics',
    'Настройки': 'Settings', 'Логи': 'Logs', 'Версия 1.0 BETA': 'Version 1.0 BETA',
    'Обход блокировок, Telegram прокси и DNS для нейросетей': 'Network access, Telegram proxy and AI DNS',
    'Стратегии, служба Windows, фильтры, списки доменов и обслуживание': 'Strategies, Windows service, filters and maintenance',
    'Поиск частых причин, по которым обход может не работать': 'Find common connection problems',
    'Запуск, поведение и внешний вид приложения': 'Startup, behaviour and appearance',
    'Вывод winws.exe, Telegram прокси и самого приложения': 'Output from winws.exe, Telegram proxy and the app',
    'ОТКЛЮЧЕНО': 'OFF', 'ВКЛЮЧЕНО': 'ON', 'ВЫКЛ': 'OFF', 'ВКЛ': 'ON',
    'Модули': 'Modules', 'нажмите на кольцо или переключатель': 'use a power button or switch',
    'Telegram прокси': 'Telegram proxy', 'DNS для нейросетей': 'DNS for AI services',
    'Подключить Telegram': 'Connect Telegram', 'Подобрать стратегию': 'Choose a strategy',
    'YouTube, Discord и др.': 'YouTube, Discord and more',
    'WebSocket-мост для Telegram Desktop': 'WebSocket bridge for Telegram Desktop',
    'Запускать вместе с Windows': 'Start with Windows',
    'свёрнуто в трей, всё включится само': 'minimised to the system tray',
    'Стратегия и режим запуска': 'Strategy and launch mode', 'Стратегия': 'Strategy',
    'Подобрать автоматически': 'Auto-select',
    'Проверяет соединение с YouTube и Discord. Проверка может занять несколько минут.': 'Tests YouTube and Discord connections. This may take several minutes.',
    'Через приложение': 'Through the app', 'Служба Windows': 'Windows service',
    'Режим запуска': 'Launch mode', 'Установить службу': 'Install service',
    'Запустить': 'Start', 'Остановить': 'Stop', 'Удалить службы': 'Remove services',
    'Перезапускать при сбое': 'Restart after failure', 'Фильтры': 'Filters',
    'Выкл': 'Off', 'TCP и UDP': 'TCP and UDP', 'Порты TCP': 'TCP ports', 'Порты UDP': 'UDP ports',
    'Сохранить': 'Save', 'Обновить список IPSet': 'Update IPSet list',
    'Свои списки': 'Custom lists', 'Домены для обхода': 'Domains to route',
    'Домены-исключения': 'Excluded domains', 'IP-исключения': 'Excluded IP addresses',
    'Сохранить и перезапустить': 'Save and restart', 'Открыть папку lists': 'Open lists folder',
    'Активные фейки': 'Active fakes', 'Заменить': 'Replace', 'Обслуживание': 'Maintenance',
    'Проверить обновления': 'Check for updates', 'Обновить zapret': 'Update zapret',
    'Тест стратегий': 'Test strategies', 'Обновить hosts': 'Update hosts',
    'Убрать записи из hosts': 'Remove hosts entries', 'Открыть папку zapret': 'Open zapret folder',
    'Проверять обновления zapret при запуске': 'Check zapret updates on startup',
    'Как подключить': 'How to connect', 'Копировать ссылку': 'Copy link', 'Открыть лог': 'Open log',
    'Подключение MTProto': 'MTProto connection', 'IP-адрес': 'IP address', 'Порт': 'Port',
    'Ключ': 'Secret', 'Новый ключ': 'New secret', 'Датацентры Telegram (DC → IP)': 'Telegram data centres (DC → IP)',
    'Дополнительно': 'Advanced', 'Тест': 'Test', 'Буфер': 'Buffer',
    'Подробное логирование': 'Verbose logging', 'Макс. размер лога': 'Max log size',
    'Проверять обновления tg-ws-proxy': 'Check tg-ws-proxy updates', 'Проверить сейчас': 'Check now',
    'Сбросить изменения': 'Discard changes', 'Сервис': 'Provider', 'Сайт сервиса': 'Provider website',
    'Режим': 'Mode', 'Авто': 'Auto', 'Системный': 'System', 'Проверка доступа': 'Check access',
    'Проверить': 'Check', 'DNS выключен': 'DNS off', 'Запустить диагностику': 'Run diagnostics',
    'Очистить кэш Discord': 'Clear Discord cache', 'Сброс сети': 'Reset network',
    'Исключения Защитника…': 'Defender exclusions…', 'Восстановить файлы zapret': 'Restore zapret files',
    'Нажмите «Запустить диагностику»': 'Select “Run diagnostics”', 'Подробнее': 'Details',
    'Запуск': 'Startup', 'При автозапуске сворачивать в трей': 'Start minimised to tray',
    'Включать zapret при запуске': 'Start zapret with the app',
    'Включать Telegram прокси при запуске': 'Start Telegram proxy with the app',
    'Поведение и вид': 'Appearance and behaviour', 'Закрытие окна сворачивает в трей': 'Close window to tray',
    'Уведомления': 'Notifications', 'Тёмная': 'Dark', 'Светлая': 'Light', 'Тема': 'Theme',
    'Полупрозрачное окно': 'Translucent window', 'О программе': 'About',
    'Открыть папку данных': 'Open data folder', 'Открыть папку логов': 'Open logs folder',
    'Копировать': 'Copy', 'Приложение': 'Application', 'Язык': 'Language',
    'Русский': 'Русский', 'English (beta)': 'English (beta)',
    'English: основной интерфейс переведён, некоторые подсказки остаются на русском.': 'English: the main interface is translated; some advanced help remains in Russian.',
    'Доступны русский и английский языки.': 'Russian and English are available.',
    'Включить всё': 'Enable all', 'Выключить всё': 'Disable all',
    'выключен': 'off', 'включён': 'on', 'работает': 'running', 'перезапуск…': 'restarting…',
    'В режиме службы Windows не используется': 'Not used in Windows service mode',
    'Сообщать о сбоях и обновлениях': 'Notify about errors and updates',
    'Открыть': 'Open', 'Закрыть': 'Close', 'Свернуть': 'Minimise', 'Развернуть': 'Maximise',
    'Обновления': 'Updates', 'Автоматически скачивать обновления': 'Automatically download updates',
    'Релизы сохраняются отдельно: архив Zapret и отдельная программа TG WS Proxy. Встроенные компоненты они не обновляют.': 'Releases are saved separately: the Zapret archive and a standalone TG WS Proxy app. They do not update the built-in components.',
    'Проверить и скачать': 'Check and download', 'Открыть папку обновлений': 'Open updates folder',
    'Версия Zapret': 'Zapret version', 'Версия Telegram WS Proxy': 'Telegram WS Proxy version',
    'Выбрать версию': 'Select version', 'Проверить обновление': 'Check for updates',
    'Перезапустить приложение': 'Restart application',
    'Скачать обновление': 'Download update', 'Обновления: проверка…': 'Updates: checking…',
    'Новые версии добавляются в список, текущая не переключается автоматически. Для обновления Telegram-прокси нужен перезапуск приложения.': 'New versions are added to the list without switching automatically. Restart the app to update Telegram proxy.',
    'Пример: 1024-1934,1936-65535': 'Example: 1024-1934,1936-65535',
}

EN.update({
    'Диагностика': 'Diagnostics', 'Локальный MTProto-прокси: соединения Telegram Desktop идут через WebSocket и Cloudflare': 'Local MTProto proxy: Telegram Desktop connects through WebSocket and Cloudflare',
    'Состояние защиты': 'Protection status', 'Соединения TG': 'TG connections', 'Отправлено': 'Uploaded', 'Получено': 'Downloaded',
    'Стратегия zapret': 'Zapret strategy', 'Трафик Telegram': 'Telegram traffic', 'за последние 2 минуты': 'last 2 minutes',
    '▲ отправка': '▲ upload', '▼ загрузка': '▼ download', '0 Б/с': '0 B/s',
    'Включить или выключить TELEGRAM': 'Turn Telegram on or off', 'Включить или выключить ZAPRET': 'Turn Zapret on or off',
    'Нажмите, чтобы включить или выключить': 'Click to turn on or off', 'ошибка': 'error',
    'Все модули работают: сайты, Telegram и нейросети доступны.': 'All modules are running: websites, Telegram and AI services are available.',
    'Всё выключено. Нажмите «Включить всё» или на кольцо модуля.': 'Everything is off. Select “Enable all” or a module power button.',
    'winws.exe восстанавливается': 'winws.exe is restarting', 'мост для Telegram Desktop': 'Telegram Desktop bridge',
    'запущен извне': 'started externally', 'winws.exe запущен не приложением': 'winws.exe was started outside the app',
    '«Через приложение» — обход работает, пока запущено приложение (рекомендуется). «Служба Windows» — как Install Service в service.bat: работает даже без приложения.': '“Through the app” runs the bypass while the app is open (recommended). “Windows service” continues running after the app closes.',
    'Выкл (none)': 'Off (none)', 'По списку (loaded)': 'Use list (loaded)', 'Любой IP (any)': 'Any IP (any)',
    'Для веб-версии Telegram и голосовых каналов Discord': 'For Telegram Web and Discord voice channels',
    'Если winws.exe неожиданно завершится, приложение запустит его снова': 'Restart winws.exe if it stops unexpectedly',
    'Если сайты не открываются — попробуйте другую стратегию (ALT, FAKE и т.д.) или запустите «Тест стратегий», чтобы найти рабочую.': 'If sites do not open, try another strategy (ALT, FAKE, etc.) or run “Test strategies”.',
    'Замена фейковых пакетов, которые используются для Discord UDP и Game Filter UDP (Replace active fakes).': 'Replace fake packets used for Discord UDP and Game Filter UDP.',
    'Обход для игр и сервисов на портах выше 1023. Если игра или программа перестала работать с zapret — выключите.': 'Bypass for games and services on ports above 1023. Turn it off if a game or app stops working with zapret.',
    'Обход сервисов по IP из ipset-all.txt. «Любой IP» — под фильтр попадает любой адрес. Если что-то перестало открываться — поставьте «Выкл».': 'Apply the bypass to IP addresses in ipset-all.txt. “Any IP” covers every address. Select “Off” if something stops working.',
    'По одному домену или IP на строку. Изменения применяются после перезапуска обхода.': 'One domain or IP per line. Restart the bypass to apply changes.',
    'Удалить службы zapret и WinDivert (Remove Services)': 'Remove the zapret and WinDivert services',
    '1. Включите прокси.  2. Нажмите «Подключить Telegram» — Telegram Desktop предложит добавить прокси, нажмите «Включить».  Если Telegram не открылся — скопируйте ссылку, отправьте её себе в «Избранное» и нажмите на неё.': '1. Enable the proxy.  2. Select “Connect Telegram” and confirm in Telegram Desktop. If Telegram does not open, copy the link, send it to Saved Messages and open it there.',
    'CF-прокси': 'CF proxy', 'Fake TLS домен': 'Fake TLS domain',
    'Адрес, на котором прокси принимает подключения.\n127.0.0.1 — только этот компьютер, 0.0.0.0 — все интерфейсы (например, для телефона в той же сети)': 'Address on which the proxy accepts connections.\n127.0.0.1 is this computer only; 0.0.0.0 is all interfaces (for example, a phone on the same network).',
    'В Telegram Desktop в настройках прокси должен быть указан тот же порт': 'Use the same port in Telegram Desktop proxy settings',
    'Секретный ключ для авторизации клиентов (32 hex-символа)': 'Client authentication secret (32 hexadecimal characters)',
    'Свой домен (вместо автоматического выбора)': 'Custom domain (instead of automatic selection)', 'не используется': 'not used',
    'По одному правилу на строку, формат: номер:IP, например 4:149.154.167.220': 'One rule per line, in number:IP format, e.g. 4:149.154.167.220',
    'Использовать Cloudflare прокси для недоступных датацентров': 'Use the Cloudflare proxy for unavailable data centres',
    'Мультиплексирование медиа (HTTP/2)': 'Media multiplexing (HTTP/2)',
    'Объединять загрузку медиа через Cloudflare в общее HTTP/2-соединение. Требуется включённый CF-прокси и TLS.': 'Combine media downloads through Cloudflare into one HTTP/2 connection. Requires the CF proxy and TLS.',
    'Домены Cloudflare Worker через запятую — прокси передаёт через них подключение к Telegram.': 'Comma-separated Cloudflare Worker domains used to connect to Telegram.',
    'Выключить TLS для CF-прокси и CF-worker': 'Disable TLS for CF proxy and CF Worker', 'Прокси будет использовать порт 80 для CF-подключений': 'Use port 80 for CF connections',
    'Маскировка под TLS-соединение к указанному домену (ссылка ee…). Обычно не нужно.': 'Imitate a TLS connection to this domain (ee… link). Usually unnecessary.',
    'Для работы за nginx/haproxy с proxy_protocol on': 'For nginx/HAProxy with proxy_protocol enabled',
    'Размер буфера приёма/передачи (по умолчанию 256 КБ)': 'Receive/send buffer size (default: 256 KB)',
    'Пул WebSocket-сессий': 'WebSocket session pool',
    'Сколько готовых соединений держать для каждого датацентра (по умолчанию 4). 0 отключает прямой маршрут DC→IP.': 'Ready connections per data centre (default: 4). Set to 0 to disable the direct DC-to-IP route.',
    'Нужно при поиске неполадок': 'Useful for troubleshooting', ' КБ': ' KB', ' МБ': ' MB',
    'ChatGPT, Claude, Gemini, Copilot, Grok и другие сервисы, закрытые для России': 'ChatGPT, Claude, Gemini, Copilot, Grok and other services unavailable in Russia',
    'ChatGPT и Sora, Gemini и NotebookLM, Claude, GitHub Copilot, DeepL, Notion, Spotify, Xbox, игры': 'ChatGPT and Sora, Gemini and NotebookLM, Claude, GitHub Copilot, DeepL, Notion, Spotify, Xbox and games',
    'ChatGPT, Claude, Microsoft Copilot, GitHub Copilot, Grok и др.': 'ChatGPT, Claude, Microsoft Copilot, GitHub Copilot, Grok and more',
    'Быстрый приватный DNS. Нейросети не разблокирует': 'Fast private DNS. Does not unblock AI services',
    'Публичный DNS Google. Нейросети не разблокирует': 'Google public DNS. Does not unblock AI services',
    'Специальный DNS отдаёт для нейросетей адреса своих прокси, поэтому сервисы перестают видеть, что вы из России. Остальной трафик идёт как обычно. Прежние настройки DNS сохраняются и возвращаются при выключении.': 'This DNS provides proxy addresses for AI services. Other traffic is unchanged. Previous DNS settings are saved and restored when disabled.',
    'Как подключать DNS': 'DNS connection mode', 'Свой DNS': 'Custom DNS', 'Укажите адреса вручную': 'Enter addresses manually', 'необязательно': 'optional',
    'https://example.com/dns-query (нужно для шифрования)': 'https://example.com/dns-query (required for encryption)',
    'Адреса сервисов иногда меняются — актуальные смотрите на их сайтах.': 'Service addresses can change; check their websites for current values.',
    '«Системный» — адреса прописываются в сетевой адаптер; на Windows 11 запросы сразу шифруются (DoH) и продолжают работать без приложения. «Через приложение» — приложение само шифрует запросы: для Windows 10 и провайдеров, которые подменяют DNS. «Авто» выбирает сам.': '“System” configures network adapters; Windows 11 encrypts requests using DoH. “Through the app” encrypts requests in the app. “Auto” chooses a mode.',
    'Показывает, из какой страны вас видит сервис. Если не RU — доступ есть.': 'Shows the country seen by each service. A non-RU result indicates access.',
    'Если в браузере включён свой «Безопасный DNS» (Chrome, Edge, Firefox, Яндекс), он обходит системный — выключите его или выберите «Использовать текущего поставщика». После включения перезапустите браузер.': 'A browser’s Secure DNS can bypass system DNS. Disable it or select the current provider, then restart the browser.',
    'Используются обычные DNS вашего провайдера': 'Your provider’s normal DNS servers are in use',
    'Через планировщик заданий с правами администратора — без запроса UAC при каждом входе': 'Uses Task Scheduler with administrator rights, without a UAC prompt on every sign-in',
    'Обход и прокси продолжают работать. Выход — через меню значка в трее.': 'The bypass and proxy keep running. Use the tray icon menu to exit.',
    'Размытие фона за окном (Windows 10/11). Выключите, если окно выглядит некорректно или видеокарта слабая.': 'Blur the background behind the window (Windows 10/11). Turn off if the window looks wrong or your GPU is slow.',
    'Объединяет две утилиты с открытым исходным кодом, их функции и стратегии не изменены:': 'Combines two open-source utilities; their functions and strategies are unchanged:',
    'Закрывает Discord и удаляет Cache, Code Cache, GPUCache': 'Closes Discord and removes Cache, Code Cache and GPUCache',
    'netsh winsock reset и др. — если не подходит ни одна стратегия': 'Reset Winsock and other network settings if no strategy works',
    'По желанию: исключить только папки с winws.exe и WinDivert, если Защитник их удаляет': 'Optionally exclude only folders containing winws.exe and WinDivert if Defender removes them',
    'Вернуть winws.exe и WinDivert, если их удалил антивирус': 'Restore winws.exe and WinDivert if antivirus removed them',
    'Проверка…': 'Checking…', 'Скопировано': 'Copied', 'Лог пуст': 'Log is empty', 'winws.exe пока ничего не вывел': 'winws.exe has not produced output yet',
    'Да': 'Yes', 'Отмена': 'Cancel', 'Применить': 'Apply', 'Удалить': 'Remove', 'Обновить': 'Update', 'Добавить': 'Add', 'Очистить': 'Clear', 'Сбросить': 'Reset',
    'Копировать ссылку прокси': 'Copy proxy link', 'Выход': 'Exit',
    'Папка zapret': 'Zapret folder', 'Проверки доступны только в Windows': 'Checks are available only on Windows',
    'Base Filtering Engine работает': 'Base Filtering Engine is running', 'Служба Base Filtering Engine не запущена': 'Base Filtering Engine service is not running',
    'Она необходима для работы zapret': 'It is required for zapret to work', 'Системный прокси не используется': 'No system proxy is in use',
    'Убедитесь, что он рабочий, или отключите его, если не используете': 'Make sure it works, or disable it if unused',
    'TCP timestamps включены': 'TCP timestamps are enabled', 'Найден Adguard — может мешать Discord': 'AdGuard detected; it may interfere with Discord', 'Adguard не найден': 'AdGuard not found',
    'Найдены службы Killer — конфликтуют с zapret': 'Killer services detected; they conflict with zapret', 'Службы Killer не найдены': 'Killer services not found',
    'Найдена Intel Connectivity Network Service — конфликтует с zapret': 'Intel Connectivity Network Service detected; it conflicts with zapret', 'Intel Connectivity Network Service не найдена': 'Intel Connectivity Network Service not found',
    'Найдены службы Check Point — конфликтуют с zapret': 'Check Point services detected; they conflict with zapret', 'Попробуйте удалить Check Point': 'Try removing Check Point', 'Check Point не найден': 'Check Point not found',
    'Найдены службы SmartByte — конфликтуют с zapret': 'SmartByte services detected; they conflict with zapret', 'Удалите или отключите SmartByte через services.msc': 'Remove or disable SmartByte using services.msc', 'SmartByte не найден': 'SmartByte not found',
    'В пути к zapret есть кириллица': 'The zapret path contains Cyrillic characters', 'Перенесите программу, например, в C:\\zapret': 'Move the program, for example to C:\\zapret', 'Путь без кириллицы': 'The path contains no Cyrillic characters',
    'zapret находится в папке OneDrive': 'Zapret is in a OneDrive folder', 'Не в папке OneDrive': 'Not in a OneDrive folder',
    'Файл WinDivert64.sys не найден': 'WinDivert64.sys not found', 'Возможно, его удалил антивирус. Добавьте папку в исключения и переустановите файлы.': 'Antivirus may have removed it. Review exclusions and restore the files.',
    'Некоторые VPN конфликтуют с zapret — отключите их на время работы обхода': 'Some VPNs conflict with zapret; disable them while using the bypass',
    'Службы VPN не найдены': 'No VPN services found', 'Защищённый DNS настроен': 'Secure DNS is configured', 'Защищённый DNS (DoH) не настроен': 'Secure DNS (DoH) is not configured',
    'Настройте безопасный DNS в браузере или в параметрах Windows 11': 'Configure Secure DNS in your browser or Windows 11 settings',
    'В hosts есть записи youtube.com / youtu.be': 'The hosts file contains youtube.com / youtu.be entries', 'Это может мешать работе YouTube': 'This may interfere with YouTube',
    'WinDivert активен, но winws.exe не запущен': 'WinDivert is active, but winws.exe is not running', 'Возможно, WinDivert занят другой программой обхода': 'Another bypass program may be using WinDivert',
    'Конфликтующих служб обхода нет': 'No conflicting bypass services found', 'Удалить WinDivert': 'Remove WinDivert', 'Удалить их': 'Remove them',
    'WinDivert удалён': 'WinDivert removed', 'WinDivert удалён после удаления конфликтующих служб': 'WinDivert removed after conflicting services were removed',
    'WinDivert всё ещё нельзя удалить — проверьте, не использует ли его другая программа обхода': 'WinDivert could not be removed; check whether another bypass program is using it',
    'Прокси остановлен': 'Proxy stopped', 'Прокси уже запущен': 'Proxy is already running', 'Прокси не запустился': 'Proxy could not start',
    'Предыдущий запуск прокси ещё завершается, попробуйте через пару секунд': 'The previous proxy instance is still stopping; try again shortly',
    'Версия Telegram-прокси не найдена': 'Telegram proxy version not found', 'Версия Telegram-прокси выбрана': 'Telegram proxy version selected',
    'Версия выбрана. Нажмите «Перезапустить приложение», чтобы применить её.': 'Version selected. Click “Restart application” to apply it.',
    'Настройки сохранены, перезапуск прокси…': 'Settings saved; restarting proxy…', 'Настройки сохранены': 'Settings saved',
    'Проверка CF-прокси…': 'Checking CF proxy…', 'Проверка Cloudflare Worker…': 'Checking Cloudflare Worker…',
    'Идёт подбор стратегии, подождите…': 'Selecting a strategy, please wait…', 'Не удалось подобрать': 'Selection failed', 'Ошибка подбора': 'Selection failed',
    'Сначала включите Telegram прокси': 'Enable the Telegram proxy first',
    'Не удалось открыть Telegram. Ссылка скопирована — отправьте её в Telegram и нажмите на неё.': 'Could not open Telegram. The link was copied; send it to Telegram and open it there.',
    'Telegram предложит добавить прокси — нажмите «Включить»': 'Telegram will offer to add the proxy; select “Enable”',
    'Ссылка скопирована. Отправьте её себе в Telegram и нажмите на неё.': 'Link copied. Send it to yourself in Telegram and open it.',
    'Проверка обновлений уже выполняется': 'An update check is already running', 'Проверяю и скачиваю обновления…': 'Checking and downloading updates…',
    'Включаю DNS…': 'Enabling DNS…', 'Возвращаю прежний DNS…': 'Restoring previous DNS…',
    'Автозапуск включён': 'Startup enabled', 'Автозапуск выключен': 'Startup disabled', 'Обновления: ошибка проверки': 'Updates: check failed',
    'Файлы zapret восстановлены': 'Zapret files restored', 'Не все файлы удалось восстановить — проверьте антивирус': 'Some files could not be restored; check your antivirus',
    'Сеть сброшена. Перезагрузите компьютер.': 'Network reset. Restart your computer.',
    'Диагностика': 'Diagnostics', 'Выход': 'Exit', 'Готово': 'Done', 'Ошибка': 'Error',
    'Обновление hosts': 'Update hosts',
    'Эти записи нужны для веб-версии Telegram и голосовых каналов Discord. Приложение добавит их отдельным блоком (его можно убрать одной кнопкой) и сохранит резервную копию hosts.': 'These entries are used for Telegram Web and Discord voice. They will be added as a separate removable block and a hosts backup will be saved.',
    'Удалить службу zapret и запускать обход через приложение?': 'Remove the zapret service and run the bypass through the app?',
    'Удалить службу': 'Remove service', 'Остановить и удалить службы zapret и WinDivert?': 'Stop and remove the zapret and WinDivert services?',
    'Скачать последнюю версию zapret с GitHub и установить её? Ваши списки, Game Filter и режим IPSet сохранятся.': 'Download and install the latest zapret from GitHub? Your lists, Game Filter and IPSet mode will be preserved.',
    'Исключения Защитника (по желанию)': 'Defender exclusions (optional)',
    'Защитник иногда помечает winws.exe и драйвер WinDivert как «HackTool» и удаляет их — тогда обход не работает. Это известное ложное срабатывание для всех сборок zapret.': 'Defender may flag and remove winws.exe and WinDivert as a HackTool, preventing the bypass from working.',
    'Будут исключены ТОЛЬКО эти папки (остальное Защитник проверяет как обычно):': 'ONLY these folders will be excluded; Defender will scan everything else as usual:',
    'Убрать исключения можно в «Безопасность Windows → Исключения».': 'You can remove exclusions in Windows Security → Exclusions.',
    'Кэш Discord': 'Discord cache', 'Закрыть Discord и очистить его кэш?': 'Close Discord and clear its cache?',
    'Будут выполнены команды:': 'The following commands will run:',
    'После этого нужно перезагрузить компьютер. Продолжить?': 'You will need to restart your computer afterwards. Continue?',
    'Переключаю версию Zapret…': 'Switching Zapret version…', 'Загрузка списка IPSet…': 'Downloading the IPSet list…',
    'Обновление zapret…': 'Updating zapret…', 'Проверка hosts…': 'Checking hosts…',
    'Нажмите «Установить службу», чтобы служба использовала новую стратегию': 'Select “Install service” to apply the new strategy to the service',
    'Неверный формат портов. Пример: 1024-1934,1936-65535': 'Invalid port format. Example: 1024-1934,1936-65535',
    'Game Filter сохранён': 'Game Filter saved', 'Списки сохранены': 'Lists saved', 'Активный фейк заменён': 'Active fake replaced',
    'Версия Zapret не найдена': 'Zapret version not found', 'Сначала отключите режим службы Zapret на вкладке Zapret.': 'First disable Zapret service mode on the Zapret tab.',
    'Обход остановлен': 'Bypass stopped', 'Служба zapret запущена': 'Zapret service started', 'Служба zapret остановлена': 'Zapret service stopped',
    'Обход перезапущен': 'Bypass restarted', 'Для службы: переустановите её, чтобы применить изменения': 'Reinstall the service to apply changes',
    'служба Windows': 'Windows service', 'служба не установлена': 'service not installed',
    'служба: работает': 'service: running', 'служба: остановлена': 'service: stopped',
    'WinDivert: нет': 'WinDivert: none', 'WinDivert: не загружен': 'WinDivert: not loaded',
    'через приложение': 'through the app', 'системный': 'system', 'нейросети доступны': 'AI services available',
    'меньше минуты': 'less than a minute',
    'Обнаружен другой winws.exe. Остановите его вручную перед запуском.': 'Another winws.exe is running. Stop it before starting.',
    'Остановите службу zapret перед автоподбором.': 'Stop the zapret service before automatic selection.',
    'Обнаружен другой winws.exe. Остановите его перед автоподбором.': 'Another winws.exe is running. Stop it before automatic selection.',
    'Стратегии не найдены.': 'No strategies found.', 'Стратегии не найдены': 'No strategies found',
    'Рабочая стратегия не найдена. Предыдущее состояние восстановлено.': 'No working strategy found. The previous state was restored.',
    'Скрипт тестов не найден': 'Test script not found',
    'Тесты запущены в отдельном окне. Обход приложения остановлен на время тестов — включите его после.': 'Tests started in a separate window. The app bypass was stopped during testing; turn it on again afterwards.',
    'Нет резервной копии списка. Сначала обновите IPSet-список.': 'No list backup exists. Update the IPSet list first.',
    'Получен пустой список': 'The downloaded list is empty', 'Файл не найден': 'File not found',
    'Домен Fake TLS должен состоять из латинских символов': 'The Fake TLS domain must use Latin characters',
    'Укажите домены Cloudflare Worker': 'Enter Cloudflare Worker domains',
    'Порт занят другой программой (возможно, запущен оригинальный TgWsProxy). Закройте её или смените порт.': 'The port is in use by another program (possibly the original TgWsProxy). Close it or change the port.',
    'Не удалось узнать адрес': 'Could not determine address', 'Локальный DNS не запустился': 'Local DNS could not start',
    'домен не резолвится': 'domain does not resolve', 'нет соединения': 'no connection',
    'Укажите хотя бы один IPv4-адрес DNS': 'Enter at least one IPv4 DNS address', 'Не найдено активных сетевых адаптеров': 'No active network adapters found',
    'DNS возвращён к прежним настройкам': 'Previous DNS settings restored',
    'Порт 53 на 127.0.0.1 занят другой программой. Используйте режим «Системный».': 'Port 53 on 127.0.0.1 is in use. Select System mode.',
    'Для режима «Через приложение» нужен адрес DoH': 'A DoH address is required for Through the app mode',
    'Сохранено': 'Saved', 'Файл hosts в репозитории пуст': 'The repository hosts file is empty', 'Файл hosts актуален': 'Hosts file is up to date',
    'Файл hosts нужно обновить': 'The hosts file needs updating', 'Записи ZapretTG удалены из hosts': 'ZapretTG entries removed from hosts',
    'Обход и прокси продолжают работать. Выход — через меню значка в трее.': 'The bypass and proxy keep running. Use the tray icon menu to exit.',
    'Приложение продолжает работать в трее. Выход — правой кнопкой по значку.': 'The app is still running in the tray. Right-click its icon to exit.',
    'Не удалось перенести данные в Program Files:': 'Could not move data to Program Files:',
    'Старая папка сохранена. Закройте программу и проверьте доступ к новой папке.': 'The old folder has been preserved. Close the app and check access to the new folder.',
    'Не удалось подготовить файлы zapret:': 'Could not prepare zapret files:',
    'Старая папка версий не должна быть ссылкой': 'The old versions folder must not be a link',
    'Папка данных не должна быть ссылкой': 'The data folder must not be a link',
    'Служба Zapret использует старую папку. Переустановите службу на вкладке Zapret, чтобы использовать новую папку.': 'The Zapret service uses the old folder. Reinstall the service on the Zapret tab to use the new folder.',
    'Запущен оригинальный TgWsProxy — он занимает порт прокси. Закройте его (значок в трее → Выход) и уберите из автозагрузки.': 'The original TgWsProxy is running and using the proxy port. Close it from the tray and remove it from startup.',
    'Готово! Обход и Telegram прокси включены. Нажмите «Подключить Telegram», чтобы добавить прокси в Telegram Desktop.': 'Ready! The bypass and Telegram proxy are enabled. Select “Connect Telegram” to add the proxy to Telegram Desktop.',
})

_PATTERNS = (
    (r'^Готово: ошибок — (\d+), предупреждений — (\d+)$', r'Complete: \1 errors, \2 warnings'),
    (r'^Включён системный прокси: (.*)$', r'System proxy enabled: \1'),
    (r'^Найдены службы VPN: (.*)$', r'VPN services found: \1'),
    (r'^Найдены конфликтующие службы обхода: (.*)$', r'Conflicting bypass services found: \1'),
    (r'^TCP timestamps были выключены — включены$', r'TCP timestamps were disabled; now enabled'),
    (r'^TCP timestamps были выключены — не удалось включить$', r'TCP timestamps were disabled and could not be enabled'),
    (r'^Прокси запущен на (.*)$', r'Proxy started on \1'),
    (r'^Выбранная версия Telegram-прокси не загрузилась\. Восстановлена версия (.*)\.$', r'The selected Telegram proxy version could not load. Version \1 was restored.'),
    (r'^Прокси завершился \((.*)\), перезапуск через (\d+) с$', r'Proxy stopped (\1); restarting in \2 s'),
    (r'^Ошибка прокси: (.*)$', r'Proxy error: \1'),
    (r'^Работает версия ([^;]+); после перезапуска: (.+)$', r'Running version \1; after restart: \2'),
    (r'^Работает версия (.+)$', r'Running version \1'),
    (r'^Встроенная версия: (.+)$', r'Built-in version: \1'),
    (r'^Основная \((.+)\)$', r'Default (\1)'),
    (r'^Версия zapret: (.*?)  ·  папка: (.*)$', r'Zapret version: \1  ·  folder: \2'),
    (r'^стратегия службы: (.*?)  ·  WinDivert: нет$', r'Service strategy: \1  ·  WinDivert: none'),
    (r'^стратегия службы: (.*?)  ·  WinDivert: не загружен$', r'Service strategy: \1  ·  WinDivert: not loaded'),
    (r'^стратегия службы: (.*?)  ·  WinDivert: (.*)$', r'Service strategy: \1  ·  WinDivert: \2'),
    (r'^стратегия (.*)$', r'strategy \1'),
    (r'^работает (\d+) д (\d+) ч$', r'running \1 d \2 h'),
    (r'^работает (\d+) ч (\d+) мин$', r'running \1 h \2 min'),
    (r'^работает (\d+) мин$', r'running \1 min'),
    (r'^работает меньше минуты$', r'running less than a minute'),
    (r'^(\d+) д (\d+) ч$', r'\1 d \2 h'),
    (r'^(\d+) ч (\d+) мин$', r'\1 h \2 min'),
    (r'^(\d+) мин$', r'\1 min'),
    (r'^(\d+) соед\.$', r'\1 connections'),
    (r'^0 Б/с$', r'0 B/s'),
    (r'^Будет использоваться: Системный \(с шифрованием DoH\)$', r'Will use: System (encrypted with DoH)'),
    (r'^Будет использоваться: Системный \(Windows 10: без шифрования\)$', r'Will use: System (Windows 10: unencrypted)'),
    (r'^Будет использоваться: Через приложение \(DoH на 127\.0\.0\.1\)$', r'Will use: Through the app (DoH on 127.0.0.1)'),
    (r'^DNS включён · (.*)$', r'DNS enabled · \1'),
    (r'^Режим: через приложение \(DoH\) · запросов: (.*)$', r'Mode: through the app (DoH) · queries: \1'),
    (r'^Режим: системный$', r'Mode: system'),
    (r'^сервис видит регион: (.*)$', r'service sees region: \1'),
    (r'^Локальный DNS: (.*)$', r'Local DNS: \1'),
    (r'^DNS включён: (.*)$', r'DNS enabled: \1'),
    (r'^Выбран (.*)\. Включите DNS переключателем сверху\.$', r'\1 selected. Enable DNS using the switch above.'),
    (r'^Переключение на (.*)…$', r'Switching to \1…'),
    (r'^Выбрана стратегия (.*)$', r'Strategy selected: \1'),
    (r'^Обход запущен: (.*)$', r'Bypass started: \1'),
    (r'^Подобрана стратегия: (.*?)\. Проверьте воспроизведение и голосовые каналы вручную\.$', r'Strategy selected: \1. Check video playback and voice channels manually.'),
    (r'^Установка службы со стратегией (.*)…$', r'Installing service with strategy \1…'),
    (r'^Выбрана версия Zapret (.*)$', r'Zapret version selected: \1'),
    (r'^Уже выбрана версия (.*)$', r'Version already selected: \1'),
    (r'^Служба zapret установлена: (.*)$', r'Zapret service installed: \1'),
    (r'^Не удалось выбрать версию: (.*)$', r'Could not select version: \1'),
    (r'^Не удалось применить настройки: (.*)$', r'Could not apply settings: \1'),
    (r'^Ошибка восстановления: (.*)$', r'Recovery failed: \1'),
    (r'^Рабочая стратегия не найдена; не удалось восстановить предыдущую: (.*)$', r'No working strategy found; could not restore the previous one: \1'),
    (r'^Не удалось запустить winws\.exe: (.*)$', r'Could not start winws.exe: \1'),
    (r'^Не удалось создать службу: (.*)$', r'Could not create service: \1'),
    (r'^Служба создана, но не запустилась: (.*)$', r'Service was created but did not start: \1'),
    (r'^Не удалось проверить обновления: (.*)$', r'Could not check for updates: \1'),
    (r'^Не удалось скачать список: (.*)$', r'Could not download the list: \1'),
    (r'^Ошибка теста: (.*)$', r'Test error: \1'),
    (r'^Ошибка подбора: (.*)$', r'Selection error: \1'),
    (r'^Ошибка обновления: (.*)$', r'Update error: \1'),
    (r'^Ошибка проверки: (.*)$', r'Check error: \1'),
    (r'^Ошибка: (.*)$', r'Error: \1'),
    (r'^Не удалось перезапустить приложение: (.*)$', r'Could not restart the application: \1'),
    (r'^Не удалось изменить автозапуск: (.*)$', r'Could not change startup settings: \1'),
    (r'^Не удалось выбрать папку: (.*)$', r'Could not select the folder: \1'),
    (r'^Не удалось открыть папку: (.*)$', r'Could not open the folder: \1'),
    (r'^В новой папке уже есть другой файл: (.*)$', r'A different file already exists in the new folder: \1'),
    (r'^Нельзя переносить ссылку: (.*)$', r'Cannot migrate a link: \1'),
    (r'^Неподдерживаемый файл: (.*)$', r'Unsupported file: \1'),
    (r'^Не удалось перенести папку загрузок: (.*)$', r'Could not migrate the downloads folder: \1'),
    (r'^Нельзя перенести файл: (.*)$', r'Cannot migrate file: \1'),
    (r'^(.+): версия добавлена\. Для применения нажмите «Перезапустить приложение» на вкладке Telegram\.$', r'\1: version added. Click “Restart application” on the Telegram tab to apply it.'),
    (r'^(.+): версия добавлена и выбрана\.$', r'\1: version added and selected.'),
    (r'^(.+): версия добавлена$', r'\1: version added'),
    (r'^(.+): актуальная версия уже работает\.$', r'\1: the latest version is already running.'),
    (r'^(.+): проверка выключена$', r'\1: checks disabled'),
    (r'^(.+): ошибка проверки$', r'\1: check failed'),
    (r'^(.+): актуально$', r'\1: up to date'),
    (r'^(.+): доступна (.+)$', r'\1: \2 available'),
    (r'^Данные: (.*)$', r'Data: \1'),
    (r'^Удалены: (.*)$', r'Removed: \1'),
    (r'^Удалено (.*)$', r'Removed \1'),
    (r'^Не удалось удалить (.*)$', r'Could not remove \1'),
    (r'^(Discord(?: PTB| Canary| Development)?) закрыт$', r'\1 closed'),
    (r'^Открыть (ZapretApp-.*)$', r'Open \1'),
)


def translate_text(text, language='en'):
    if language != 'en' or not isinstance(text, str):
        return text
    if text in EN:
        return EN[text]
    if '\n' in text:
        return '\n'.join(translate_text(line, language) for line in text.split('\n'))
    if text.startswith('Telegram прокси: '):
        return 'Telegram proxy: ' + translate_text(text[len('Telegram прокси: '):], language)
    if text.startswith('DNS: '):
        return 'DNS: ' + translate_text(text[len('DNS: '):], language)
    if text.startswith('Выключено: ') and text.endswith('.'):
        return 'Off: ' + text[len('Выключено: '):].replace('Telegram прокси', 'Telegram proxy')
    for pattern, replacement in _PATTERNS:
        if re.fullmatch(pattern, text):
            return re.sub(pattern, replacement, text)
    # Status rows combine separately translatable descriptions with a bullet.
    if ' · ' in text:
        return ' · '.join(translate_text(part, language) for part in text.split(' · '))
    if re.fullmatch(r'(?:[▲▼] )?[\d.,]+\s*(?:ТБ|ГБ|МБ|КБ|Б)(?:/с)?(?: [▲▼] [\d.,]+\s*(?:ТБ|ГБ|МБ|КБ|Б))?', text):
        return text.replace('ТБ', 'TB').replace('ГБ', 'GB').replace('МБ', 'MB').replace('КБ', 'KB').replace('Б', 'B').replace('/с', '/s')
    return text


def saved_language():
    """Read the last selected language for errors that occur before Config loads."""
    from ..paths import CONFIG_FILE, DATA_NAME
    old = Path(os.environ.get('ProgramData') or r'C:\ProgramData') / DATA_NAME / 'config.json'
    for path in (CONFIG_FILE, old):
        try:
            value = json.loads(path.read_text(encoding='utf-8')).get('app', {}).get('language')
            if value in ('ru', 'en'):
                return value
        except (OSError, ValueError, AttributeError, TypeError):
            continue
    return 'ru'


def _translate(widget, getter, setter, key, language):
    text = getter()
    source = widget.property('_ru_' + key)
    rendered = widget.property('_shown_' + key)
    if source is None or text != rendered:
        source = text
        widget.setProperty('_ru_' + key, source)
    shown = translate_text(source, language)
    if shown != text:
        setter(shown)
    widget.setProperty('_shown_' + key, shown)

def apply_language(root, language):
    for cls in (QLabel, QAbstractButton):
        for obj in root.findChildren(cls):
            _translate(obj, obj.text, obj.setText, 'text', language)
    for combo in root.findChildren(QComboBox):
        for index in range(combo.count()):
            _translate(combo, lambda i=index: combo.itemText(i),
                       lambda value, i=index: combo.setItemText(i, value), f'item{index}', language)
    for tabs in root.findChildren(QTabWidget):
        for index in range(tabs.count()):
            _translate(tabs, lambda i=index: tabs.tabText(i),
                       lambda value, i=index: tabs.setTabText(i, value), f'tab{index}', language)
    for field in root.findChildren(QLineEdit):
        _translate(field, field.placeholderText, field.setPlaceholderText, 'placeholder', language)
    for field in root.findChildren(QSpinBox):
        _translate(field, field.suffix, field.setSuffix, 'suffix', language)
    for widget in root.findChildren(QWidget):
        if widget.toolTip():
            _translate(widget, widget.toolTip, widget.setToolTip, 'tooltip', language)
    for action in root.findChildren(QAction):
        if action.text():
            _translate(action, action.text, action.setText, 'action', language)

# Financial Interview Bot

Telegram бот для проведения финансовых интервью с интеграцией GigaChat для консультаций.

## 🚀 Возможности

- 🎤 Интерактивные финансовые интервью
- 💡 Консультации с GigaChat
- 📊 Сохранение ответов в PostgreSQL
- 📈 Экспорт данных в CSV
- ⏱ Отслеживание времени прохождения
- 🌍 Поддержка московского времени

## 📋 Требования

- Python 3.8+
- PostgreSQL (для локального запуска)
- Telegram Bot Token
- GigaChat API ключ

## 🛠 Установка

### Локальная установка

1. **Клонируйте репозиторий:**
git clone https://github.com/your-username/financial-interview-bot.git
cd financial-interview-bot
text

2. **Создайте виртуальное окружение:**
python -m venv interview_bot_env
source interview_bot_env/bin/activate # Linux/Mac
text

3. **Установите зависимости:**
pip install -r requirements.txt
text

4. **Настройте PostgreSQL:**
createdb interview_bot_db
text

5. **Настройте переменные окружения:**
cp .env.example .env
Отредактируйте .env файл, добавив ваши ключи

text

6. **Инициализируйте базу данных:**
python test_extended_database.py
python add_test_data.py
python add_more_questions.py
text

7. **Запустите бота:**
python run_bot.py
text

### 🔧 Запуск в Google Colab

Установка зависимостей

!pip install psycopg2-binary SQLAlchemy python-dotenv pyTelegramBotAPI pytz gigachat
Клонирование репозитория

!git clone https://github.com/your-username/financial-interview-bot.git
%cd financial-interview-bot
Настройка переменных окружения

import os
os.environ['TELEGRAM_BOT_TOKEN'] = 'your_token_here'
os.environ['GIGACHAT_CREDENTIALS'] = 'your_credentials_here'
os.environ['DATABASE_URL'] = 'sqlite:///interview_bot.db'
Создание базы данных и запуск

!python test_extended_database.py
!python add_test_data.py
!python add_more_questions.py
!python run_bot.py
text

## 🔑 Получение ключей

### Telegram Bot Token
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

### GigaChat Credentials
1. Перейдите на [developers.sber.ru](https://developers.sber.ru/)
2. Зарегистрируйтесь и создайте проект
3. Получите ключ авторизации для GigaChat API

## 📱 Команды бота

- `/start` - начать новое интервью
- `/end` - завершить текущее интервью
- `/status` - показать прогресс интервью
- `/help` - справка по использованию

## 📊 Анализ данных

- `python view_collected_data.py` - подробный анализ
- `python quick_stats.py` - быстрая статистика
- `python export_data.py` - экспорт в CSV
- `python check_responses.py` - проверка ответов

## 📁 Структура проекта

```
financial-interview-bot/
├── modules/
│   ├── database.py          # Работа с базой данных
│   ├── telegram_handler.py  # Telegram бот
│   └── gigachat_handler.py  # Интеграция с GigaChat
├── run_bot.py              # Запуск бота
├── add_test_data.py        # Добавление тестовых данных
├── add_more_questions.py   # Дополнительные вопросы
├── export_data.py          # Экспорт данных
├── view_collected_data.py  # Просмотр данных
├── check_responses.py      # Проверка ответов
├── quick_stats.py          # Быстрая статистика
├── clean_output.py         # Очистка папки output
├── test_extended_database.py # Тест базы данных
├── tests/                  # Тесты
├── requirements.txt        # Зависимости
├── .env.example           # Шаблон переменных окружения
└── README.md              # Документация
```

## 📄 Лицензия

MIT License

## 🆘 Поддержка

При возникновении проблем создайте Issue в репозитории.

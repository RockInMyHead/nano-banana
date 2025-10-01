# 🎨 NanaBanana Generator

Современный генератор изображений на базе FastAPI и Google Gemini 2.5 Flash Image Preview API.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Особенности

- 🚀 **Быстрая генерация** - использует Google Gemini 2.5 Flash Image Preview API
- 🎨 **Современный интерфейс** - адаптивный дизайн с интуитивным управлением
- 📱 **Мобильная поддержка** - полностью адаптивный интерфейс
- 🖼️ **Галерея изображений** - просмотр всех сгенерированных изображений
- 💾 **Управление файлами** - скачивание, копирование, регенерация
- ⚡ **Асинхронность** - FastAPI для высокой производительности
- 📊 **Метаданные** - подробная информация о каждом изображении
- 🔒 **Безопасность** - API ключи через переменные окружения

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/RockInMyHead/nano-banana.git
cd nano-banana
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка API ключа

Создайте файл `.env` в корне проекта:

```bash
# Google Gemini API Key
GEMINI_API_KEY=ваш_ключ_от_google
```

**Как получить API ключ:**
1. Перейдите на https://makersuite.google.com/app/apikey
2. Войдите в аккаунт Google
3. Создайте новый API ключ
4. Скопируйте ключ в файл `.env`

### 4. Запуск приложения

```bash
python main.py
```

Приложение будет доступно по адресу: http://localhost:8083

## 🎯 Функциональность

### Генерация изображений
- Ввод текстового описания (промпт)
- Выбор размера изображения (512px - 1536px)
- Асинхронная генерация с индикатором загрузки
- Автоматическое сохранение на сервере

### Галерея и управление
- Просмотр всех сгенерированных изображений
- Детальная информация (размер, промпт, время генерации)
- Скачивание изображений
- Копирование в буфер обмена
- Регенерация с теми же параметрами
- Поделиться изображениями

### API эндпоинты
- `GET /` - Главная страница
- `POST /generate` - Генерация изображения
- `POST /save_image` - Сохранение изображения
- `GET /images` - Список всех изображений
- `GET /generated_images/{filename}` - Просмотр изображения
- `GET /download/{filename}` - Скачивание изображения

## 🛠️ Технические детали

### Архитектура
- **Backend**: FastAPI (асинхронный)
- **Frontend**: Vanilla JavaScript + HTML5 + CSS3
- **API**: Google Gemini 2.5 Flash Image Preview
- **Обработка изображений**: Pillow (PIL)
- **Хранение**: Локальная файловая система

### Структура проекта
```
nano-banana/
├── app.py              # Основное FastAPI приложение
├── main.py             # Точка входа
├── requirements.txt    # Зависимости Python
├── .env               # Переменные окружения (создать)
├── .gitignore         # Исключения для Git
├── README.md          # Документация проекта
├── SETUP.md           # Инструкции по настройке
├── templates/
│   └── index.html     # HTML шаблон
├── static/
│   └── script.js      # JavaScript логика
└── generated_images/  # Папка с изображениями
    └── metadata.json  # Метаданные изображений
```

## 📋 Требования

- Python 3.11+
- Google Gemini API ключ
- Интернет-соединение

## 🔧 Установка зависимостей

```bash
pip install fastapi uvicorn jinja2 httpx python-dotenv pillow
```

## 🚨 Устранение неполадок

### Ошибка "GEMINI_API_KEY not set"
- Убедитесь, что файл `.env` создан
- Проверьте правильность API ключа
- Перезапустите приложение

### Ошибка генерации изображений
- Проверьте интернет-соединение
- Убедитесь, что API ключ действителен
- Проверьте лимиты API в Google Cloud Console

### Проблемы с отображением
- Очистите кэш браузера
- Проверьте консоль браузера на ошибки JavaScript

## 📝 Логи

Приложение ведет подробные логи. Для отладки проверьте вывод в терминале.

## 🔄 Обновления

Для обновления зависимостей:
```bash
pip install -r requirements.txt --upgrade
```

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для получения дополнительной информации.

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! Пожалуйста:

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Отправьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте раздел "Устранение неполадок"
2. Создайте Issue в GitHub
3. Опишите проблему подробно

## 🎉 Благодарности

- Google за предоставление Gemini API
- FastAPI за отличный фреймворк
- Всем контрибьюторам проекта

---

**Создано с ❤️ для генерации красивых изображений**

[![GitHub stars](https://img.shields.io/github/stars/RockInMyHead/nano-banana.svg?style=social&label=Star)](https://github.com/RockInMyHead/nano-banana)
[![GitHub forks](https://img.shields.io/github/forks/RockInMyHead/nano-banana.svg?style=social&label=Fork)](https://github.com/RockInMyHead/nano-banana/fork)
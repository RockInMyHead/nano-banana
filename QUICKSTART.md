# 🚀 Быстрый старт NanaBanana

## ✅ Приложение запущено!

Ваше приложение работает в Docker контейнере и доступно по адресу:

### 🌐 http://localhost:8083

---

## 📦 Управление Docker контейнером

### Просмотр статуса
```bash
docker-compose ps
```

### Просмотр логов
```bash
docker-compose logs -f
```

### Остановка приложения
```bash
docker-compose down
```

### Запуск приложения
```bash
docker-compose up -d
```

### Перезапуск приложения
```bash
docker-compose restart
```

### Пересборка и запуск (после изменений в коде)
```bash
docker-compose up -d --build
```

---

## 📁 Файлы Docker

- `Dockerfile` - конфигурация Docker образа
- `docker-compose.yml` - конфигурация запуска контейнера
- `.dockerignore` - исключения при сборке образа
- `DOCKER.md` - полная документация по Docker

---

## 💡 Полезные команды

### Зайти в контейнер
```bash
docker exec -it nanabanana-app /bin/bash
```

### Очистить все Docker ресурсы
```bash
docker system prune -a
```

### Посмотреть использование ресурсов
```bash
docker stats nanabanana-app
```

---

## 🔑 API Ключ

Если нужно установить свой Gemini API ключ:

1. Откройте файл `.env`
2. Добавьте строку: `GEMINI_API_KEY=ваш_ключ`
3. Перезапустите контейнер: `docker-compose restart`

---

## 📸 Сохранение изображений

Все изображения сохраняются в папке `generated_images/` и доступны даже после перезапуска контейнера.

---

**Примечание:** Чтобы быстро настроить глобальный доступ через ngrok, используйте скрипт `start-global.sh`:
```bash
./start-global.sh
```

---

**Приятного использования! 🎨**

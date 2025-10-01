# 🐳 Docker инструкция для NanaBanana

## 🚀 Быстрый запуск

### 1. Убедитесь, что у вас установлен Docker
```bash
docker --version
docker-compose --version
```

### 2. Создайте файл .env с вашим API ключом

```bash
echo "GEMINI_API_KEY=ваш_ключ_от_google" > .env
```

### 3. Запуск через Docker Compose (рекомендуется)

```bash
docker-compose up -d
```

Приложение будет доступно по адресу: http://localhost:8083

### 4. Остановка приложения

```bash
docker-compose down
```

## 📦 Альтернативный запуск через Docker

### Сборка образа
```bash
docker build -t nanabanana .
```

### Запуск контейнера
```bash
docker run -d \
  --name nanabanana-app \
  -p 8083:8083 \
  -v $(pwd)/generated_images:/app/generated_images \
  -e GEMINI_API_KEY=ваш_ключ \
  nanabanana
```

### Просмотр логов
```bash
docker logs -f nanabanana-app
```

### Остановка контейнера
```bash
docker stop nanabanana-app
```

### Удаление контейнера
```bash
docker rm nanabanana-app
```

## 🔄 Обновление приложения

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📊 Полезные команды

### Просмотр работающих контейнеров
```bash
docker ps
```

### Просмотр логов
```bash
docker-compose logs -f
```

### Вход в контейнер
```bash
docker exec -it nanabanana-app /bin/bash
```

### Очистка неиспользуемых образов
```bash
docker system prune -a
```

## 💾 Том для сохранения изображений

По умолчанию папка `generated_images` монтируется как volume, поэтому все изображения будут сохраняться на вашем компьютере и не потеряются при перезапуске контейнера.

## 🌐 Развертывание на сервере

Для развертывания на удаленном сервере:

1. Склонируйте репозиторий на сервер
2. Создайте `.env` файл с API ключом
3. Запустите `docker-compose up -d`
4. Настройте nginx/traefik для проксирования (опционально)

### Пример nginx конфигурации

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8083;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 🔒 Безопасность

- **Никогда** не коммитьте `.env` файл с API ключом в Git
- Используйте переменные окружения для чувствительных данных
- На production используйте HTTPS

## ❓ Устранение неполадок

### Контейнер не запускается
```bash
docker-compose logs
```

### Порт уже занят
Измените порт в `docker-compose.yml`:
```yaml
ports:
  - "8084:8083"  # Измените первое число
```

### Проблемы с правами доступа к volume
```bash
chmod 755 generated_images
```

## 📝 Примечания

- Приложение запускается на порту 8083 внутри контейнера
- Папка `generated_images` автоматически синхронизируется между контейнером и хостом
- При остановке контейнера изображения остаются на диске

---

**Создано с ❤️ для удобного развертывания**

#!/usr/bin/env bash
set -e

# Сборка и запуск Docker контейнеров
echo "Сборка и запуск Docker контейнеров..."
docker-compose up -d --build

# Запуск ngrok, если он еще не запущен
if ! pgrep -x ngrok > /dev/null; then
  echo "Запуск ngrok туннеля..."
  ngrok http 8083 --log=stdout > /tmp/ngrok.log 2>&1 &
  sleep 3
fi

# Получение публичного URL из ngrok API
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c 'import sys, json; obj = json.load(sys.stdin); print(obj.get("tunnels", [])[0].get("public_url", ""))')

echo "Приложение доступно по адресу: $PUBLIC_URL"

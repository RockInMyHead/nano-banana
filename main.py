from app import app

if __name__ == "__main__":
    import uvicorn
    print("🚀 Запуск веб-сервиса генерации изображений...")
    print("📱 Откройте браузер: http://localhost:8083")
    uvicorn.run(app, host="0.0.0.0", port=8083)




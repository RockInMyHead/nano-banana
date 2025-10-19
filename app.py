from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import httpx
import base64
import uuid
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageOps
from io import BytesIO

# Загружаем переменные из .env файла
load_dotenv()
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Конфигурация Gemini API
GEMINI_MODEL = "gemini-2.5-flash-image-preview"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyABXLCOQx43FNOetOJNZNmxMhTmU33W7Rs"

# Папка для сохранения изображений
UPLOAD_FOLDER = 'generated_images'
METADATA_FILE = os.path.join(UPLOAD_FOLDER, 'metadata.json')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def load_metadata():
    """Загружает метаданные изображений"""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_metadata(metadata):
    """Сохраняет метаданные изображений"""
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения метаданных: {e}")

def add_image_metadata(filename, width, height, prompt, model, generation_time):
    """Добавляет метаданные для нового изображения"""
    metadata = load_metadata()
    metadata[filename] = {
        'width': width,
        'height': height,
        'prompt': prompt,
        'model': model,
        'generation_time': generation_time,
        'created': datetime.now().isoformat()
    }
    save_metadata(metadata)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(request: Request):
    if API_KEY is None:
        logger.error("GEMINI_API_KEY not set")
        return JSONResponse({"error": "Server misconfiguration: GEMINI_API_KEY not set"}, status_code=500)
    
    try:
        data = await request.json()
        prompt = data.get("prompt")
        width = data.get("width", 1024)
        height = data.get("height", 1024)
        if not prompt:
            return JSONResponse({"error": "Prompt missing"}, status_code=400)

        # Формируем улучшенный промпт с указанием размера
        enhanced_prompt = f"{prompt}\n\nСоздайте изображение размером {width}x{height} пикселей. Изображение должно точно соответствовать указанным размерам {width}x{height}."
        
        # Формируем тело запроса для Gemini API
        payload = {
            "contents": [
                {
                    "parts": [
                        { "text": enhanced_prompt }
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(GEMINI_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            resp_json = resp.json()
            logger.info(f"Gemini response: {resp_json}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return JSONResponse({"error": f"HTTP Error: {e.response.status_code} — {e.response.text}"}, status_code=500)
    except Exception as e:
        logger.exception("Unexpected error in generate")
        return JSONResponse({"error": f"Internal error: {str(e)}"}, status_code=500)

    # Разбор ответа
    # ищем первую часть с inline_data — это изображение
    for candidate in resp_json.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                # данные base64
                img_b64 = inline["data"]
                # чтобы передать на фронт, можно вернуть base64 строку
                return JSONResponse({"image_b64": img_b64})

    return JSONResponse({"error": "No image in response"}, status_code=500)

@app.post("/save_image")
async def save_image(request: Request):
    """Сохраняет изображение из base64 на сервере"""
    try:
        data = await request.json()
        image_b64 = data.get("image_b64")
        prompt = data.get("prompt", "Unknown prompt")
        width = data.get("width", 1024)
        height = data.get("height", 1024)
        
        if not image_b64:
            return JSONResponse({"error": "No image data provided"}, status_code=400)
        
        # Декодируем base64
        try:
            image_data = base64.b64decode(image_b64)
        except Exception as e:
            return JSONResponse({"error": f"Invalid base64 data: {str(e)}"}, status_code=400)
        
        # Создаем уникальное имя файла
        filename = f"image_{uuid.uuid4().hex[:8]}_{int(time.time())}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Обрабатываем изображение с помощью PIL
        try:
            with Image.open(BytesIO(image_data)) as img:
                # Конвертируем в RGB если нужно
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Получаем исходные размеры
                original_width, original_height = img.size
                logger.info(f"Original image size: {original_width}x{original_height}")
                logger.info(f"Target size: {width}x{height}")
                
                # Проверяем, нужно ли изменять размер
                if original_width != width or original_height != height:
                    logger.info(f"Resizing image from {original_width}x{original_height} to {width}x{height}")
                    
                    # Масштабируем изображение с сохранением пропорций
                    # Сначала определяем коэффициент масштабирования
                    scale_w = width / original_width
                    scale_h = height / original_height
                    scale = min(scale_w, scale_h)  # Используем меньший коэффициент для сохранения пропорций
                    
                    # Убеждаемся, что изображение поместится в указанные размеры
                    if scale > 1.0:
                        scale = min(scale_w, scale_h)  # Не увеличиваем больше чем нужно
                    else:
                        scale = min(scale_w, scale_h)  # Уменьшаем если нужно
                    
                    # Вычисляем новые размеры
                    new_width = int(original_width * scale)
                    new_height = int(original_height * scale)
                    
                    logger.info(f"Scaling by factor {scale:.3f} to {new_width}x{new_height}")
                    
                    # Масштабируем изображение
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Создаем новое изображение нужного размера с белым фоном
                    final_img = Image.new('RGB', (width, height), (255, 255, 255))
                    
                    # Вычисляем позицию для центрирования
                    x_offset = (width - new_width) // 2
                    y_offset = (height - new_height) // 2
                    
                    # Вставляем масштабированное изображение в центр
                    final_img.paste(img, (x_offset, y_offset))
                    img = final_img
                    
                    logger.info(f"Image scaled and centered to {width}x{height}")
                else:
                    logger.info("Image size matches target, no resizing needed")
                
                # Сохраняем как PNG с максимальным качеством
                img.save(filepath, 'PNG', optimize=True, quality=95)
                actual_width, actual_height = img.size
                logger.info(f"Final image size: {actual_width}x{actual_height}")
                
        except Exception as e:
            # Если PIL не может обработать, сохраняем как есть
            with open(filepath, 'wb') as f:
                f.write(image_data)
            actual_width, actual_height = width, height
        
        # Добавляем метаданные
        generation_time = 0  # Время генерации уже прошло
        add_image_metadata(filename, actual_width, actual_height, prompt, "Gemini 2.5 Flash", generation_time)
        
        # Размер файла
        file_size = os.path.getsize(filepath)
        
        return JSONResponse({
            "success": True,
            "filename": filename,
            "width": actual_width,
            "height": actual_height,
            "model": "Gemini 2.5 Flash",
            "generation_time": generation_time,
            "file_size": file_size,
            "prompt": prompt,
            "created": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.exception("Error saving image")
        return JSONResponse({"error": f"Error saving image: {str(e)}"}, status_code=500)

@app.get("/images")
async def list_images():
    """Возвращает список всех сгенерированных изображений"""
    try:
        metadata = load_metadata()
        images = []
        
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.png'):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(filepath):
                    file_size = os.path.getsize(filepath)
                    
                    # Получаем метаданные
                    img_metadata = metadata.get(filename, {})
                    
                    images.append({
                        'filename': filename,
                        'size': file_size,
                        'width': img_metadata.get('width', 'Unknown'),
                        'height': img_metadata.get('height', 'Unknown'),
                        'prompt': img_metadata.get('prompt', 'Unknown'),
                        'model': img_metadata.get('model', 'Unknown'),
                        'generation_time': img_metadata.get('generation_time', 0),
                        'created': img_metadata.get('created', 'Unknown')
                    })
        
        # Сортируем по дате создания (новые сначала)
        images.sort(key=lambda x: x['created'], reverse=True)
        
        return JSONResponse({'images': images})
        
    except Exception as e:
        logger.exception("Error listing images")
        return JSONResponse({"error": f"Error listing images: {str(e)}"}, status_code=500)

@app.get("/generated_images/{filename}")
async def serve_image(filename: str):
    """Отдает изображение по имени файла"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            return FileResponse(filepath)
        else:
            raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        logger.exception(f"Error serving image {filename}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")

@app.get("/download/{filename}")
async def download_image(filename: str):
    """Скачивание изображения"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            return FileResponse(
                filepath, 
                media_type='application/octet-stream',
                filename=filename
            )
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.exception(f"Error downloading image {filename}")
        raise HTTPException(status_code=500, detail=f"Error downloading image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Запуск веб-сервиса генерации изображений...")
    print("📱 Откройте браузер: http://localhost:8083")
    uvicorn.run(app, host="0.0.0.0", port=8083)
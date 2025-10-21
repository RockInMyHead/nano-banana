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
import asyncio

# Загружаем переменные из .env файла
load_dotenv()
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Конфигурация Gemini API
GEMINI_MODEL = "gemini-2.5-flash-image"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyABXLCOQx43FNOetOJNZNmxMhTmU33W7Rs"

# Временное отключение генерации изображений
ENABLE_IMAGE_GENERATION = True
IMAGE_GENERATION_MESSAGE = "🎨 Генерация изображений временно недоступна из-за ограничений API. Попробуйте позже."

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

async def fill_black_borders(img, prompt: str) -> Image.Image:
    """Заполняет черные полосы сгенерированным контентом"""
    # Конвертируем в RGB для анализа
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Получаем размеры изображения
    width, height = img.size
    
    # Анализируем черные области (сверху/снизу и слева/справа)
    black_threshold = 30
    border_size = int(min(width, height) * 0.05)  # 5% от меньшей стороны
    
    # Проверяем верхнюю область
    top_black = False
    if border_size > 0:
        top_pixels = sum(1 for x in range(width) for y in range(min(border_size, height))
                        if all(img.getpixel((x, y))[c] < black_threshold for c in range(3)))
        top_black = top_pixels > (width * border_size * 0.8)  # 80% черных пикселей
    
    # Проверяем нижнюю область
    bottom_black = False
    if border_size > 0 and height > border_size:
        bottom_pixels = sum(1 for x in range(width) for y in range(max(0, height - border_size), height)
                           if all(img.getpixel((x, y))[c] < black_threshold for c in range(3)))
        bottom_black = bottom_pixels > (width * border_size * 0.8)
    
    # Проверяем левую область
    left_black = False
    if border_size > 0:
        left_pixels = sum(1 for x in range(min(border_size, width)) for y in range(height)
                         if all(img.getpixel((x, y))[c] < black_threshold for c in range(3)))
        left_black = left_pixels > (border_size * height * 0.8)
    
    # Проверяем правую область
    right_black = False
    if border_size > 0 and width > border_size:
        right_pixels = sum(1 for x in range(max(0, width - border_size), width) for y in range(height)
                          if all(img.getpixel((x, y))[c] < black_threshold for c in range(3)))
        right_black = right_pixels > (border_size * height * 0.8)
    
    # Если нет черных областей, возвращаем оригинал
    if not (top_black or bottom_black or left_black or right_black):
        logger.info("Черные полосы не обнаружены")
        return img
    
    logger.info(f"Обнаружены черные полосы: верх={top_black}, низ={bottom_black}, лево={left_black}, право={right_black}")
    
    try:
        # Конвертируем изображение в base64 для отправки в Gemini
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_b64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Формируем специфичный промпт в зависимости от типа черных полос
        border_types = []
        if top_black:
            border_types.append("top")
        if bottom_black:
            border_types.append("bottom")
        if left_black:
            border_types.append("left")
        if right_black:
            border_types.append("right")
        
        border_description = ", ".join(border_types)
        extend_prompt = f"Extend the image to fill the black border areas on the {border_description} side(s) with matching content from the original scene. Seamlessly continue the existing composition. {prompt}"
        
        # Отправляем запрос в Gemini с изображением
        payload = {
            "contents": [
                {
                    "parts": [
                        { "text": extend_prompt },
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": img_b64
                            }
                        }
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
            
            # Извлекаем расширенное изображение из ответа
            for candidate in resp_json.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    inline = part.get("inlineData") or part.get("inline_data")
                    if inline and inline.get("data"):
                        extended_data = base64.b64decode(inline["data"])
                        with Image.open(BytesIO(extended_data)) as extended_img:
                            extended_img = extended_img.convert('RGB')
                            # Масштабируем до нужного размера
                            result = extended_img.resize((width, height), Image.Resampling.LANCZOS)
                            logger.info("Изображение успешно расширено")
                            return result
            
            raise Exception("No extended image in response")
            
    except Exception as e:
        logger.error(f"Ошибка расширения изображения: {e}")
        return img

async def generate_image_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Генерирует изображение с повторными попытками при ошибках квоты"""
    for attempt in range(max_retries):
        try:
            # Формируем тело запроса для Gemini API
            payload = {
                "contents": [
                    {
                        "parts": [
                            { "text": prompt }
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
                
                if resp.status_code == 429:
                    # Обрабатываем ошибку квоты
                    error_data = resp.json()
                    retry_after = 60  # По умолчанию 60 секунд
                    
                    # Пытаемся извлечь время ожидания из ошибки
                    try:
                        details = error_data.get("error", {}).get("details", [])
                        for detail in details:
                            if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                                retry_info = detail.get("retryDelay", "")
                                if retry_info.endswith("s"):
                                    retry_after = int(float(retry_info[:-1]))
                                    break
                    except:
                        pass
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"Quota exceeded, retrying in {retry_after} seconds (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        raise Exception(f"Quota exceeded after {max_retries} attempts")
                
                resp.raise_for_status()
                resp_json = resp.json()
                
                # Извлекаем изображение из ответа
                for candidate in resp_json.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        inline = part.get("inlineData") or part.get("inline_data")
                        if inline and inline.get("data"):
                            return inline["data"]
                
                raise Exception("No image in response")
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                if attempt < max_retries - 1:
                    continue
                else:
                    raise Exception(f"HTTP Error: {e.response.status_code} — {e.response.text}")
            else:
                raise Exception(f"HTTP Error: {e.response.status_code} — {e.response.text}")
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Error on attempt {attempt + 1}, retrying: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                raise

@app.post("/generate")
async def generate(request: Request):
    if API_KEY is None:
        logger.error("GEMINI_API_KEY not set")
        return JSONResponse({"error": "Server misconfiguration: GEMINI_API_KEY not set"}, status_code=500)
    
    # Проверяем, включена ли генерация изображений
    if not ENABLE_IMAGE_GENERATION:
        return JSONResponse({"error": IMAGE_GENERATION_MESSAGE}, status_code=503)
    
    try:
        data = await request.json()
        prompt = data.get("prompt")
        if not prompt:
            return JSONResponse({"error": "Prompt missing"}, status_code=400)

        # Используем функцию с повторными попытками
        img_b64 = await generate_image_with_retry(prompt)
        return JSONResponse({"image_b64": img_b64})
        
    except Exception as e:
        logger.exception("Unexpected error in generate")
        return JSONResponse({"error": f"Internal error: {str(e)}"}, status_code=500)

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
                
                original_size = img.size
                logger.info(f"Исходный размер изображения от Gemini: {original_size}")
                logger.info(f"Целевой размер: {width}x{height}")

                # Изменяем размер с сохранением пропорций БЕЗ обрезки
                # Вычисляем коэффициент масштабирования (уменьшаем, чтобы поместилось)
                ratio = min(width / original_size[0], height / original_size[1])
                new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                
                # Масштабируем изображение
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Размер после масштабирования: {img.size}")
                
                # Создаем новое изображение целевого размера с черным фоном
                result = Image.new('RGB', (width, height), (0, 0, 0))
                
                # Вычисляем позицию для центрирования
                paste_x = (width - new_size[0]) // 2
                paste_y = (height - new_size[1]) // 2
                
                # Вставляем масштабированное изображение по центру
                result.paste(img, (paste_x, paste_y))
                logger.info(f"Изображение вставлено в позицию: ({paste_x}, {paste_y})")
                
                # Заполняем черные полосы сгенерированным контентом
                result = await fill_black_borders(result, prompt)
                
                logger.info(f"Финальный размер: {result.size}")

                # Сохраняем как PNG
                result.save(filepath, 'PNG')
                actual_width, actual_height = result.size
                
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
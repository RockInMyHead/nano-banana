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

def get_aspect_ratio(width, height):
    """Определяет ближайшее допустимое соотношение сторон для Gemini API"""
    # Допустимые соотношения сторон API
    allowed = ['1:1','2:3','3:2','3:4','4:3','4:5','5:4','9:16','16:9','21:9']
    # Текущее соотношение
    target = width / height
    # Вычисляем ближайшее значение
    best = allowed[0]
    best_diff = float('inf')
    for ar in allowed:
        a, b = map(int, ar.split(':'))
        ratio = a / b
        diff = abs(ratio - target)
        if diff < best_diff:
            best_diff = diff
            best = ar
    return best

def generate_prompt_for_size(prompt: str, width: int, height: int) -> str:
    """Генерирует расширенный промпт с указанием размера"""
    return f"{prompt}\n\nIMPORTANT: Fill the entire frame completely. No black bars, no letterboxing, no pillarboxing. The image should extend to all edges of the canvas."

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
        ref_image = data.get("ref_image")
        # Определяем аспект-рацию, возможно с использованием референс-изображения
        if ref_image:
            ref_path = os.path.join(UPLOAD_FOLDER, ref_image)
            try:
                with Image.open(ref_path) as img_ref:
                    ref_w, ref_h = img_ref.size
            except Exception:
                return JSONResponse({"error": f"Reference image not found: {ref_image}"}, status_code=400)
            aspect_ratio = get_aspect_ratio(ref_w, ref_h)
            ref_instruction = "Use the uploaded image's aspect ratio as the final frame; fill all its area; no letterboxing."
            logger.info(f"Using reference image aspect ratio: {aspect_ratio}")
        else:
            aspect_ratio = get_aspect_ratio(width, height)
            ref_instruction = "Fill the entire frame; no black bars or letterboxing."

        if not prompt:
            return JSONResponse({"error": "Prompt missing"}, status_code=400)

        # Генерируем расширенный промпт под размер изображения
        enhanced_prompt = generate_prompt_for_size(prompt, width, height)
        # Добавляем инструкцию по референс-изображению
        if ref_instruction:
            enhanced_prompt += f"\n\n{ref_instruction}"

        requested_ratio = width / height
        logger.info(f"Requested size: {width}x{height} (ratio: {requested_ratio:.3f})")
        logger.info(f"Using API aspect ratio: {aspect_ratio}")

        # Формируем тело запроса для Gemini API
        payload = {
            "contents": [
                {
                    "parts": [
                        { "text": enhanced_prompt }
                    ]
                }
            ],
            "generationConfig": {
                "imageConfig": {
                    "aspectRatio": aspect_ratio
                },
                "responseModalities": ["IMAGE"]
            }
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

                # Получаем исходные размеры от API
                original_width, original_height = img.size
                logger.info(f"Original image size from API: {original_width}x{original_height}")
                logger.info(f"Requested size: {width}x{height}")

                # НЕ изменяем размер изображения от API!
                # API уже сгенерировал изображение с оптимальным aspect ratio
                # Изменение размера может привести к черным полосам или обрезанию

                # Сохраняем изображение как есть от API
                img.save(filepath, 'PNG', optimize=True, quality=95)
                actual_width, actual_height = img.size
                logger.info(f"Saved image with original API size: {actual_width}x{actual_height}")

        except Exception as e:
            # Если PIL не может обработать, сохраняем как есть
            logger.warning(f"PIL processing failed, saving raw data: {e}")
            with open(filepath, 'wb') as f:
                f.write(image_data)
            # Пытаемся определить размер
            try:
                with Image.open(filepath) as img:
                    actual_width, actual_height = img.size
            except:
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
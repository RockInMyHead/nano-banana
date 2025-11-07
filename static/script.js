// Глобальные переменные
let currentImageData = null;
let currentImageInfo = null;

// Основная функция генерации изображения
async function generateImage() {
    const prompt = document.getElementById('prompt').value.trim();
    const width = parseInt(document.getElementById('width').value);
    const height = parseInt(document.getElementById('height').value);
    
    // Валидация
    if (!prompt) {
        showError('Пожалуйста, введите описание изображения');
        return;
    }
    
    if (prompt.length < 3) {
        showError('Описание должно содержать минимум 3 символа');
        return;
    }
    
    // Валидация размеров
    if (!width || !height) {
        showError('Пожалуйста, укажите размеры изображения');
        return;
    }
    
    if (width < 256 || width > 2048 || height < 256 || height > 2048) {
        showError('Размеры должны быть от 256 до 2048 пикселей');
        return;
    }
    
    // Показываем загрузку
    showLoading(true);
    hideError();
    hideSuccess();
    
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                width: width,
                height: height
            })
    });

    const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }
        
        if (data.image_b64) {
            // Сохраняем изображение на сервере
            const saveResponse = await saveImage(data.image_b64, prompt, width, height);
            
            if (saveResponse.success) {
                currentImageData = data.image_b64;
                currentImageInfo = saveResponse;
                displayGeneratedImage(data.image_b64, saveResponse);
                showSuccess(`Изображение создано за ${saveResponse.generation_time?.toFixed(2) || 'неизвестно'} секунд`);
                
                // Обновляем галерею
                loadGallery();
            } else {
                throw new Error(saveResponse.error || 'Ошибка сохранения изображения');
            }
        } else {
            throw new Error('Сервер не вернул изображение');
        }
        
    } catch (error) {
        console.error('Ошибка генерации:', error);
        showError(`Ошибка генерации: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Функция сохранения изображения на сервере
async function saveImage(imageB64, prompt, width, height) {
    try {
        const response = await fetch('/save_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_b64: imageB64,
                prompt: prompt,
                width: width,
                height: height
            })
        });
        
        return await response.json();
    } catch (error) {
        console.error('Ошибка сохранения:', error);
        return { success: false, error: error.message };
    }
}

// Отображение сгенерированного изображения
function displayGeneratedImage(imageB64, imageInfo) {
    const resultSection = document.getElementById('resultSection');
    const resultDiv = document.getElementById('result');
    
    // Используем сохранённый файл для отображения с учетом ресайза
    const imageUrl = `/generated_images/${imageInfo.filename}`;
    
    resultDiv.innerHTML = `
        <img src="${imageUrl}" alt="Сгенерированное изображение" class="generated-image">
        <div class="image-info">
            <h3>Информация об изображении</h3>
            <p><strong>Размер:</strong> ${imageInfo.width} × ${imageInfo.height} пикселей</p>
            <p><strong>Промпт:</strong> ${imageInfo.prompt}</p>
            <p><strong>Модель:</strong> ${imageInfo.model || 'Gemini 2.5 Flash'}</p>
            <p><strong>Время генерации:</strong> ${imageInfo.generation_time?.toFixed(2) || 'неизвестно'} сек</p>
            <p><strong>Размер файла:</strong> ${formatFileSize(imageInfo.file_size || 0)}</p>
            <p><strong>Создано:</strong> ${new Date(imageInfo.created || Date.now()).toLocaleString('ru-RU')}</p>
        </div>
        <div class="action-buttons">
            <button class="btn btn-primary" onclick="downloadImage('${imageInfo.filename}')">
                💾 Скачать
            </button>
            <button class="btn btn-success" onclick="copyImageToClipboard()">
                📋 Копировать
            </button>
            <button class="btn btn-info" onclick="shareImage()">
                🔗 Поделиться
            </button>
        </div>
    `;
    
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// Загрузка галереи изображений
async function loadGallery() {
    const gallery = document.getElementById('gallery');
    gallery.innerHTML = '<div style="text-align: center; padding: 20px;">Загрузка галереи...</div>';
    
    try {
        const response = await fetch('/images');
        const data = await response.json();
        
        if (data.images && data.images.length > 0) {
            displayGallery(data.images);
        } else {
            gallery.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">Галерея пуста. Создайте первое изображение!</div>';
        }
    } catch (error) {
        console.error('Ошибка загрузки галереи:', error);
        gallery.innerHTML = '<div style="text-align: center; padding: 20px; color: #dc3545;">Ошибка загрузки галереи</div>';
    }
}

// Отображение галереи
function displayGallery(images) {
    const gallery = document.getElementById('gallery');
    
    gallery.innerHTML = images.map(image => `
        <div class="gallery-item">
            <img src="/generated_images/${image.filename}" alt="${image.prompt}" 
<<<<<<< HEAD
                 onerror="this.onerror=null;this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='">
=======
                 onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuKEliDQt9C90LDRh9C10L3QuNC1INC40L3RgtC10YDQtdC90L3QvtCz0L4g0L/RgNC+0LTQvtC70L7QstC+0LrQsA==</text></svg>'">
>>>>>>> 03d73daf58c1fca28a972b093ae4e025564d01e1
            <div class="gallery-item-info">
                <h4>${truncateText(image.prompt, 50)}</h4>
                <p><strong>Размер:</strong> ${image.width} × ${image.height}</p>
                <p><strong>Модель:</strong> ${image.model}</p>
                <p><strong>Время:</strong> ${image.generation_time?.toFixed(2) || 'неизвестно'}с</p>
                <p><strong>Создано:</strong> ${new Date(image.created).toLocaleDateString('ru-RU')}</p>
                <div class="gallery-actions">
                    <button class="btn btn-primary" onclick="downloadImage('${image.filename}')">
                        💾
                    </button>
                    <button class="btn btn-info" onclick="viewImage('${image.filename}')">
                        👁️
                    </button>
                    <button class="btn btn-success" onclick="regenerateImage('${image.prompt}', ${image.width}, ${image.height})">
                        🔄
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Скачивание изображения
function downloadImage(filename) {
    window.open(`/download/${filename}`, '_blank');
}

// Просмотр изображения в полном размере
function viewImage(filename) {
    window.open(`/generated_images/${filename}`, '_blank');
}

// Регенерация изображения с теми же параметрами
function regenerateImage(prompt, width, height) {
    document.getElementById('prompt').value = prompt;
    document.getElementById('width').value = width;
    document.getElementById('height').value = height;
    generateImage();
}

// Копирование изображения в буфер обмена
async function copyImageToClipboard() {
    if (!currentImageData) {
        showError('Нет изображения для копирования');
        return;
    }
    
    try {
        // Конвертируем base64 в blob
        const response = await fetch(`data:image/png;base64,${currentImageData}`);
        const blob = await response.blob();
        
        // Копируем в буфер обмена
        await navigator.clipboard.write([
            new ClipboardItem({ 'image/png': blob })
        ]);
        
        showSuccess('Изображение скопировано в буфер обмена!');
    } catch (error) {
        console.error('Ошибка копирования:', error);
        showError('Не удалось скопировать изображение');
    }
}

// Поделиться изображением
function shareImage() {
    if (!currentImageData) {
        showError('Нет изображения для публикации');
        return;
    }
    
    const imageUrl = `data:image/png;base64,${currentImageData}`;
    const shareText = `Посмотрите на это изображение, созданное с помощью ИИ: "${currentImageInfo?.prompt || 'Неизвестный промпт'}"`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Изображение, созданное ИИ',
            text: shareText,
            url: window.location.href
        }).catch(console.error);
    } else {
        // Fallback - копируем ссылку
        navigator.clipboard.writeText(shareText + '\n' + window.location.href).then(() => {
            showSuccess('Ссылка скопирована в буфер обмена!');
        }).catch(() => {
            showError('Не удалось поделиться изображением');
        });
    }
}

// Вспомогательные функции
function showLoading(show) {
    const loading = document.getElementById('loading');
    const generateBtn = document.getElementById('generateBtn');
    
    if (show) {
        loading.style.display = 'block';
        generateBtn.disabled = true;
        generateBtn.textContent = '⏳ Генерация...';
    } else {
        loading.style.display = 'none';
        generateBtn.disabled = false;
        generateBtn.textContent = '🚀 Сгенерировать изображение';
    }
}

function showError(message) {
    hideError();
    hideSuccess();
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.id = 'errorMessage';
    errorDiv.textContent = message;
    
    const generatorSection = document.querySelector('.generator-section');
    generatorSection.appendChild(errorDiv);
}

function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function showSuccess(message) {
    hideError();
    hideSuccess();
    
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.id = 'successMessage';
    successDiv.textContent = message;
    
    const generatorSection = document.querySelector('.generator-section');
    generatorSection.appendChild(successDiv);
    
    // Автоматически скрываем через 5 секунд
    setTimeout(hideSuccess, 5000);
}

function hideSuccess() {
    const successDiv = document.getElementById('successMessage');
    if (successDiv) {
        successDiv.remove();
    }
}

function truncateText(text, maxLength) {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Функция для округления размера до кратного 64
function roundToMultiple64(value) {
    return Math.round(value / 64) * 64;
}

<<<<<<< HEAD

// Функция показа информации о размере
function showSizeInfo(width, height) {
    const aspectRatio = (width / height).toFixed(2);
    const megapixels = ((width * height) / 1000000).toFixed(1);
    
    let sizeInfo = document.getElementById('sizeInfo');
    if (!sizeInfo) {
        sizeInfo = document.createElement('div');
        sizeInfo.id = 'sizeInfo';
        sizeInfo.className = 'size-info';
        document.querySelector('.generator-section').appendChild(sizeInfo);
    }
    
    sizeInfo.innerHTML = `
        <strong>📐 Информация о размере:</strong><br>
        Размер: ${width} × ${height} пикселей<br>
        Соотношение сторон: ${aspectRatio}:1<br>
        Мегапиксели: ${megapixels} MP
    `;
}

=======
>>>>>>> 03d73daf58c1fca28a972b093ae4e025564d01e1
// Обработка Enter в поле ввода
document.addEventListener('DOMContentLoaded', function() {
    const promptInput = document.getElementById('prompt');
    if (promptInput) {
        promptInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                generateImage();
            }
        });
    }
    
    // Автоматическое округление размеров при вводе
    const widthInput = document.getElementById('width');
    const heightInput = document.getElementById('height');
    
    if (widthInput) {
        widthInput.addEventListener('blur', function() {
<<<<<<< HEAD
            updateSizeInfo();
=======
            const value = parseInt(this.value);
            if (value && value % 64 !== 0) {
                const rounded = roundToMultiple64(value);
                this.value = rounded;
                showSuccess(`Ширина округлена до ${rounded}px (кратно 64)`);
                setTimeout(hideSuccess, 3000);
            }
>>>>>>> 03d73daf58c1fca28a972b093ae4e025564d01e1
        });
    }
    
    if (heightInput) {
        heightInput.addEventListener('blur', function() {
<<<<<<< HEAD
            updateSizeInfo();
=======
            const value = parseInt(this.value);
            if (value && value % 64 !== 0) {
                const rounded = roundToMultiple64(value);
                this.value = rounded;
                showSuccess(`Высота округлена до ${rounded}px (кратно 64)`);
                setTimeout(hideSuccess, 3000);
            }
>>>>>>> 03d73daf58c1fca28a972b093ae4e025564d01e1
        });
    }
    
    // Загружаем галерею при загрузке страницы
    loadGallery();
<<<<<<< HEAD
});

// Функция обновления информации о размере
function updateSizeInfo() {
    const width = parseInt(document.getElementById('width').value);
    const height = parseInt(document.getElementById('height').value);
    
    if (width && height) {
        showSizeInfo(width, height);
    }
}
=======
});
>>>>>>> 03d73daf58c1fca28a972b093ae4e025564d01e1

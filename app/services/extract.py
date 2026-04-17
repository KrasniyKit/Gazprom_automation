#!/usr/bin/env python3
"""
Модуль оцифровки паспортов оборудования: PDF -> Изображения -> Qwen2.5-VL -> JSON
"""

import base64
import json
import re
import tempfile
from pathlib import Path
from dataclasses import dataclass

import fitz  # PyMuPDF
import ollama


# =============================================================================
# КОНФИГУРАЦИЯ И ПРОМПТ
# =============================================================================

@dataclass
class ExtractorConfig:
    model: str = "qwen2.5vl:7b"
    api_base: str = "http://localhost:11434"
    pdf_dpi: int = 200  # Оптимальное DPI для скорости и качества Vision-моделей


SYSTEM_PROMPT_PATH = Path("app/prompts/system/extractor_llm.txt")
SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text().encode("utf-8")


# =============================================================================
# КЛАССЫ ЛОГИКИ (SOLID / KISS)
# =============================================================================

class ExtractionError(Exception):
    """Базовая ошибка экстракции."""
    pass


class PDFRenderer:
    """Конвертирует байты PDF в список строк Base64 (изображений)."""
    
    @staticmethod
    def to_base64_images(pdf_bytes: bytes, dpi: int = 200) -> list[str]:
        if not pdf_bytes:
            raise ExtractionError("Пустые байты PDF.")
            
        images_b64 = []
        try:
            # Открываем PDF напрямую из байтов!
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            for page in doc:
                pix = page.get_pixmap(dpi=dpi)
                img_bytes = pix.tobytes("png")
                # Кодируем картинку в Base64 строку
                b64_str = base64.b64encode(img_bytes).decode("utf-8")
                images_b64.append(b64_str)
                
            doc.close()
        except Exception as e:
            raise ExtractionError(f"Ошибка рендеринга PDF: {e}")
            
        return images_b64




class PassportExtractor:
    """
    Отвечает за общение с Vision LLM и парсинг ответа.
    """

    def __init__(self, config: ExtractorConfig):
        self._config = config
        self._client = ollama.Client(host=config.api_base)

    def extract(self, image_b64: list[Path]) -> dict:
        if not image_b64:
            raise ExtractionError("Список изображений пуст.")

        raw_content = self._call_vlm(image_b64)
        return self._parse_json(raw_content)

    def _call_vlm(self, image_b64: list[Path]) -> str:
        try:
            response = self._client.chat(
                model=self._config.model,
                format='json',  # Принудительный JSON-режим Ollama
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": "Проанализируй страницы паспорта оборудования и извлеки данные.",
                        # Магия Ollama: передаем пути к файлам, она сама делает Base64
                        "images": [str(p) for p in image_b64]  
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            raise ExtractionError(f"Ошибка вызова Ollama API: {e}")

    @staticmethod
    def _parse_json(content: str) -> dict:
        text = content.strip()
        # Очистка от маркдаун-тегов (если модель отвалилась от format='json')
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?\s*```$', '', text).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Фолбэк: пытаемся вырезать первый попавшийся объект { ... }
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
            raise ExtractionError("Модель вернула невалидный JSON.")


# =============================================================================
# ОРКЕСТРАТОР (Точка входа)
# =============================================================================

def process_passport_bytes(pdf_bytes: bytes, filename: str = "upload.pdf") -> dict:
    """
    Полный пайплайн: принимает байты PDF, возвращает готовый JSON.
    """
    pdf_path = Path(pdf_path)
    config = ExtractorConfig()
    extractor = PassportExtractor(config)

    print(f"📄 Рендеринг PDF в память: {pdf_path.name}...")
    image_b64 = PDFRenderer.to_base64_images(pdf_bytes, dpi=config.pdf_dpi)
    print(f"🖼 Сконвертировано страниц: {len(image_b64)}")

    print("🧠 Отправка в Qwen2.5-VL для анализа (это может занять несколько секунд)...")
    raw_data = extractor.extract(image_b64)

    # Добавляем системные метаданные (source), которые LLM не должна генерировать
    raw_data["source"] = {
        "file_name": filename,
        "page_count": len(image_b64),
        "ocr_engine": f"ollama-{config.model}"
    }

    print("✅ Данные успешно извлечены!")
    return raw_data



# =============================================================================
# ТЕСТОВЫЙ ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    # Укажите путь к вашему PDF файлу здесь
    test_pdf = "data/raw/Приложение 1 к задаче 1 Паспорт без заводского номера.pdf"
    
    if not Path(test_pdf).exists():
        print(f"❌ Файл не найден: {test_pdf}")
        print("Пожалуйста, укажите правильный путь к PDF файлу в переменной `test_pdf`")
    else:
        result = process_passport_pdf(test_pdf)
        print("\n📋 Результат (JSON):")
        print(json.dumps(result, ensure_ascii=False, indent=2))

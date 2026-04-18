#!/usr/bin/env python3
"""
Модуль оцифровки: PDF -> PaddleOCR -> Qwen2.5 (Text LLM) -> JSON (ГОСТ 2.601-2013)
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass

import fitz  # PyMuPDF 
import numpy as np
import ollama
from paddleocr import PaddleOCR

from app.core.schemas import PassportResponseSchema

# =============================================================================
# КОНФИГУРАЦИЯ И ПРОМПТ
# =============================================================================

@dataclass
class ExtractorConfig:
    model: str = "qwen2.5:7b"  # ТЕПЕРЬ ТЕКСТОВАЯ МОДЕЛЬ! (Не vl)
    api_base: str = "http://localhost:11434"
    pdf_dpi: int = 200


SYSTEM_PROMPT_PATH = Path("app/prompts/system/extractor_llm.txt")
try:
    SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    SYSTEM_PROMPT = "Извлеки данные из текста."


# =============================================================================
# КЛАССЫ ЛОГИКИ
# =============================================================================

class ExtractionError(Exception):
    pass


class PDFRenderer:
    """Конвертирует байты PDF в список Numpy-массивов (картинок для OCR)."""
    
    @staticmethod
    def to_numpy_images(pdf_bytes: bytes, dpi: int = 200) -> list[np.ndarray]:
        if not pdf_bytes:
            raise ExtractionError("Пустые байты PDF.")
            
        images = []
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                pix = page.get_pixmap(dpi=dpi)
                # Конвертируем pixmap в numpy array (PaddleOCR ест только numpy/PIL)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                images.append(img)
            doc.close()
        except Exception as e:
            raise ExtractionError(f"Ошибка рендеринга PDF: {e}")
            
        return images


class OCRExtractor:
    """Отвечает за распознавание текста через PaddleOCR."""
    
    def __init__(self):
        # use_angle_cls=True — поворачивает текст, если скан кривой
        # show_log=False — убирает спам в консоли
        self._ocr = PaddleOCR(use_angle_cls=True, lang='ru', show_log=False)

    def extract_text(self, images: list[np.ndarray]) -> str:
        if not images:
            raise ExtractionError("Список изображений пуст.")

        full_text = []
        try:
            for img in images:
                result = self._ocr.ocr(img, cls=True)
                if not result or not result[0]:
                    continue
                
                # Сортируем блоки по Y (сверху вниз), затем по X (слева направо)
                # Это сохраняет логическую структуру чтения документа
                lines = sorted(result[0], key=lambda x: (x[0][0][1], x[0][0][0]))
                
                for line in lines:
                    text = line[1][0]  # Сам текст
                    full_text.append(text)
                    
        except Exception as e:
            raise ExtractionError(f"Ошибка PaddleOCR: {e}")

        return "\n".join(full_text)


class PassportExtractor:
    """Отвечает за общение с текстовой LLM и парсинг ответа."""

    def __init__(self, config: ExtractorConfig):
        self._config = config
        self._client = ollama.Client(host=config.api_base)

    def extract(self, ocr_text: str) -> dict:
        if not ocr_text.strip():
            raise ExtractionError("OCR вернул пустой текст.")
        raw_content = self._call_llm(ocr_text)
        return self._parse_json(raw_content)

    def _call_llm(self, ocr_text: str) -> str:
        try:
            response = self._client.chat(
                model=self._config.model,
                format='json',
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user", 
                        "content": f"Вот сырой текст из OCR паспорта оборудования:\n\n{ocr_text}"
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            raise ExtractionError(f"Ошибка вызова Ollama API: {e}")

    @staticmethod
    def _parse_json(content: str) -> dict:
        text = content.strip()
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?\s*```$', '', text).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
            raise ExtractionError("Модель вернула невалидный JSON.")


# =============================================================================
# ОРКЕСТРАТОР
# =============================================================================

def process_passport_bytes(pdf_bytes: bytes, filename: str = "upload.pdf") -> dict:
    """
    Полный пайплайн: PDF -> Numpy -> OCR -> LLM -> Валидированный JSON.
    """
    config = ExtractorConfig()
    renderer = PDFRenderer()
    ocr = OCRExtractor()
    extractor = PassportExtractor(config)

    print(f"📄 Рендеринг PDF: {filename}...")
    images = renderer.to_numpy_images(pdf_bytes, dpi=config.pdf_dpi)
    print(f"🖼 Сконвертировано страниц: {len(images)}")

    print("🔤 Запуск PaddleOCR...")
    ocr_text = ocr.extract_text(images)
    print(f"📝 OCR извлек {len(ocr_text)} символов текста.")

    print("🧠 Отправка текста в Qwen2.5 для извлечения полей ГОСТ...")
    raw_data = extractor.extract(ocr_text)

    # Добавляем системные метаданные
    raw_data["source"] = {
        "file_name": filename,
        "page_count": len(images),
        "ocr_engine": "paddleocr + qwen2.5"
    }

    # Валидация по ГОСТ схеме
    try:
        validated_passport = PassportResponseSchema.model_validate(raw_data)
        print("✅ Данные успешно извлечены и провалидированы!")
        return validated_passport.model_dump(mode="json")
    except Exception as e:
        raise ExtractionError(f"Данные не соответствуют схеме ГОСТ: {e}")
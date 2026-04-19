#!/usr/bin/env python3
"""
Модуль оцифровки: PDF -> Qwen2.5-VL (Vision LLM) -> JSON (ГОСТ 2.601-2013)
"""

import base64
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
import ollama

from app.core.schemas import PassportResponseSchema


def _read_pdf_dpi() -> int:
    raw_value = os.getenv("PDF_DPI", "170")
    try:
        dpi = int(raw_value)
    except ValueError:
        return 170
    return min(max(dpi, 100), 300)


@dataclass
class ExtractorConfig:
    model: str = os.getenv("OLLAMA_MODEL", "qwen2.5vl:7b")
    api_base: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    pdf_dpi: int = _read_pdf_dpi()


SYSTEM_PROMPT_PATH = Path("app/prompts/system/extractor_llm.txt")
try:
    SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    SYSTEM_PROMPT = "Извлеки данные из изображений документа."


class ExtractionError(Exception):
    pass


class PDFRenderer:
    """Конвертирует байты PDF в PNG-изображения (base64) для Vision LLM."""

    @staticmethod
    def to_base64_png_images(pdf_bytes: bytes, dpi: int = 170) -> list[str]:
        if not pdf_bytes:
            raise ExtractionError("Пустые байты PDF.")

        images: list[str] = []
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                pix = page.get_pixmap(dpi=dpi)
                png_bytes = pix.tobytes("png")
                images.append(base64.b64encode(png_bytes).decode("utf-8"))
            doc.close()
        except Exception as e:
            raise ExtractionError(f"Ошибка рендеринга PDF: {e}")

        return images


_OLLAMA_CLIENTS: dict[str, ollama.Client] = {}

STRING_FIELDS_WITH_EMPTY_DEFAULT = (
    "purpose",
    "technical_specs",
    "normative_docs",
    "passport_number",
    "completeness",
    "service_life",
    "warranty",
)


def get_ollama_client(api_base: str) -> ollama.Client:
    client = _OLLAMA_CLIENTS.get(api_base)
    if client is None:
        client = ollama.Client(host=api_base)
        _OLLAMA_CLIENTS[api_base] = client
    return client


def _normalize_raw_data(raw_data: dict) -> dict:
    normalized = dict(raw_data)

    for field in STRING_FIELDS_WITH_EMPTY_DEFAULT:
        value = normalized.get(field)
        if value is None:
            normalized[field] = ""
        elif not isinstance(value, str):
            normalized[field] = str(value)

    for required_field in ("equipment_name", "manufacturer"):
        value = normalized.get(required_field)
        if value is None:
            normalized[required_field] = "UNKNOWN"
        elif not isinstance(value, str):
            normalized[required_field] = str(value)
        elif not value.strip():
            normalized[required_field] = "UNKNOWN"

    issue_date = normalized.get("issue_date")
    if issue_date == "":
        normalized["issue_date"] = None

    uncertain_fields = normalized.get("uncertain_fields")
    if uncertain_fields is None:
        normalized["uncertain_fields"] = []

    return normalized


class PassportExtractor:
    """Отвечает за общение с Vision LLM и парсинг ответа."""

    def __init__(self, config: ExtractorConfig):
        self._config = config
        self._client = get_ollama_client(config.api_base)

    def extract(self, page_images: list[str]) -> dict:
        if not page_images:
            raise ExtractionError("PDF не содержит страниц для анализа.")
        raw_content = self._call_llm(page_images)
        return self._parse_json(raw_content)

    def _call_llm(self, page_images: list[str]) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Проанализируй все страницы PDF-паспорта на изображениях и верни "
                    "структурированный JSON строго по схеме."
                ),
                "images": page_images,
            },
        ]
        try:
            response = self._client.chat(
                model=self._config.model,
                format="json",
                messages=messages,
            )
            return response["message"]["content"]
        except Exception as e:
            if self._is_missing_model_error(e):
                self._pull_model()
                try:
                    response = self._client.chat(
                        model=self._config.model,
                        format="json",
                        messages=messages,
                    )
                    return response["message"]["content"]
                except Exception as retry_error:
                    raise ExtractionError(f"Ошибка вызова Ollama API после загрузки модели: {retry_error}")
            raise ExtractionError(f"Ошибка вызова Ollama API: {e}")

    def _pull_model(self) -> None:
        try:
            self._client.pull(model=self._config.model, stream=False)
        except Exception as e:
            raise ExtractionError(f"Не удалось загрузить модель {self._config.model}: {e}")

    @staticmethod
    def _is_missing_model_error(error: Exception) -> bool:
        error_text = str(error).lower()
        return "model" in error_text and "not found" in error_text

    @staticmethod
    def _parse_json(content: str) -> dict:
        text = content.strip()
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?\s*```$", "", text).strip()

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


def process_passport_bytes(pdf_bytes: bytes, filename: str = "upload.pdf") -> dict:
    """
    Полный пайплайн: PDF -> PNG страницы -> Vision LLM -> Валидированный JSON.
    """
    config = ExtractorConfig()
    renderer = PDFRenderer()
    extractor = PassportExtractor(config)

    print(f"📄 Рендеринг PDF: {filename}...")
    page_images = renderer.to_base64_png_images(pdf_bytes, dpi=config.pdf_dpi)
    print(f"🖼 Сконвертировано страниц: {len(page_images)}")

    print("🧠 Отправка изображений в Qwen2.5-VL для извлечения полей ГОСТ...")
    raw_data = _normalize_raw_data(extractor.extract(page_images))

    raw_data["source"] = {
        "file_name": filename,
        "page_count": len(page_images),
        "ocr_engine": "qwen2.5-vl",
    }

    try:
        validated_passport = PassportResponseSchema.model_validate(raw_data)
        print("✅ Данные успешно извлечены и провалидированы!")
        return validated_passport.model_dump(mode="json")
    except Exception as e:
        raise ExtractionError(f"Данные не соответствуют схеме ГОСТ: {e}")

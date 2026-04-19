from __future__ import annotations

from pydantic import ValidationError

from backend.app.core.schemas import PassportResponseSchema
from app.exceptions import LLMExtractionError


def _patch_missing_fields(data: dict) -> None:
    """Подстраховка: исправляет пустые обязательные поля, если LLM их упустила."""
    if not data.get("passport_number"):
        data["passport_number"] = "UNKNOWN"
    if not data.get("manufacturer"):
        data["manufacturer"] = "UNKNOWN"
    
    items_block = data.get("items", {})
    for item in items_block.get("items", []):
        if not item.get("name"):
            item["name"] = "UNKNOWN"
        if not item.get("passport_number"):
            item["passport_number"] = data["passport_number"]
        if "factory_number" in item and item["factory_number"] == "":
            item["factory_number"] = None


def validate_and_enrich(
    raw_data: dict,
    file_name: str,
    page_count: int,
    ocr_engine: str = "ollama",
    ocr_confidence: float = 0.0,
) -> PassportResponseSchema:
    """
    Обогащает данные метаданными source, чинит пустые поля 
    и валидирует через Pydantic схему.
    """
    # 1. Инъекция системных метаданных
    raw_data["source"] = {
        "file_name": file_name,
        "page_count": page_count,
        "ocr_engine": ocr_engine,
        "ocr_confidence": ocr_confidence,
    }

    # 2. Защита от невалидных данных (подстраховка LLM)
    _patch_missing_fields(raw_data)

    # 3. Строгая валидация Pydantic
    try:
        return PassportResponseSchema.model_validate(raw_data)
    except ValidationError as e:
        raise LLMExtractionError(f"Ошибка валидации Pydantic: {e}") from e
from __future__ import annotations

import ollama
import json
import re
from dataclasses import dataclass
from typing import Any


from app.exceptions import LLMConnectionError, LLMResponseParseError


@dataclass
class LLMConfig:
    """Конфигурация для LLM (KISS: используем dataclass вместо тяжелых моделей)."""
    model: str = "ollama_chat/qwen2.5:7b"
    api_base: str = "http://localhost:11434"
    temperature: float = 0.0


class LLMExtractor:
    """
    Извлекает структурированные данные (dict) из сырого текста через LLM.
    SOLID: Единственная ответственность — вызов LLM и парсинг JSON.
    """

    def __init__(self, model: str = "qwen2.5vl:7b", api_base: str = "http://localhost:11434"):
        self._model = model
        # Инициализируем клиент Ollama
        self._client = ollama.Client(host=api_base)

    def extract(self, system_prompt: str, ocr_text: str) -> dict[str, Any]:
        raw_content = self._call_llm(system_prompt, ocr_text)
        return self._parse_json_response(raw_content)

    def _call_llm(self, system_prompt: str, user_text: str) -> str:
        try:
            response = completion(
                model=self._config.model,
                api_base=self._config.api_base,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=self._config.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMConnectionError(f"Ошибка вызова LLM API: {e}") from e

    @staticmethod
    def _parse_json_response(content: str) -> dict[str, Any]:
        """Очищает markdown-обертку и парсит JSON (DRY: логика в одном месте)."""
        text = re.sub(r'^```(?:json)?\s*\n?', '', content.strip())
        text = re.sub(r'\n?\s*```$', '', text).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: попытка вырезать первый попавшийся объект { ... }
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end > start:
                try:
                    return json.loads(text[start: end + 1])
                except json.JSONDecodeError:
                    pass
            
            raise LLMResponseParseError("LLM не вернул валидный JSON-объект")
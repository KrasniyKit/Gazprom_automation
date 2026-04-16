# maximum_accuracy_pipeline.py

import base64
import json
import re
import io
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from openai import OpenAI

class MaxAccuracyPipeline:
    
    def __init__(self):
        self.client = OpenAI(
            base_url="http://ollama:11434/v1",
            api_key="ollama"
        )
        self.model = "qwen2.5vl:7b"
    
    def process(self, pdf_path: Path) -> dict:
        
        # Рендерим все страницы в высоком качестве
        pages = convert_from_path(
            str(pdf_path),
            dpi=300  # высокий DPI для мелкого текста
        )
        
        # Шаг 1: Определяем тип документа по первой странице
        doc_type = self._detect_doc_type(pages[0])
        print(f"Тип документа: {doc_type}")
        
        # Шаг 2: Извлекаем данные с каждой страницы
        page_results = []
        for i, page in enumerate(pages):
            print(f"Страница {i+1}/{len(pages)}")
            result = self._extract_page(page, doc_type, i+1)
            page_results.append(result)
        
        # Шаг 3: Объединяем всё
        merged = self._merge(page_results)
        
        # Шаг 4: Второй проход — верификация
        # Смотрим на первую страницу ещё раз
        # и проверяем что ничего не пропустили
        verified = self._verify(pages[0], merged)
        
        return verified
    
    # ─────────────────────────────────────────────────────
    # ШАГ 1: Определение типа документа
    # ─────────────────────────────────────────────────────
    
    def _detect_doc_type(self, first_page: Image) -> str:
        
        prompt = """
        Посмотри на этот документ.
        
        Определи тип документа. Выбери ОДНО из:
        - passport         (паспорт отдельного устройства/компонента)
        - manual           (руководство или инструкция по эксплуатации)
        - cabinet_list     (перечень документации шкафа — список оборудования)
        - warranty         (гарантийный талон)
        - acceptance       (акт приёмки)
        
        Верни ТОЛЬКО одно слово из списка выше. Без пояснений.
        """
        
        response = self._call_model(first_page, prompt, max_tokens=20)
        
        doc_type = response.strip().lower()
        valid_types = {"passport", "manual", "cabinet_list", "warranty", "acceptance"}
        
        return doc_type if doc_type in valid_types else "passport"
    
    # ─────────────────────────────────────────────────────
    # ШАГ 2: Извлечение данных со страницы
    # ─────────────────────────────────────────────────────
    
    def _extract_page(self, page: Image, doc_type: str, page_num: int) -> dict:
        
        # Выбираем промпт под тип документа
        prompt = self._get_prompt(doc_type, page_num)
        
        response = self._call_model(page, prompt, max_tokens=3000)
        return self._parse_json(response)
    
    def _get_prompt(self, doc_type: str, page_num: int) -> str:
        
        base = """
        Извлеки ВСЕ данные которые видишь на этой странице.
        Верни ТОЛЬКО валидный JSON. Без пояснений. Без markdown.
        Ключи на русском через нижнее подчёркивание.
        Не придумывай данные которых нет на странице.
        Если страница содержит только схему или чертёж без текста — верни {}.
        """
        
        prompts = {
            
            "passport": base + """
            Это паспорт оборудования. Ищи:
            - наименование устройства (обычно в заголовке)
            - модель / артикул / код заказа
            - заводской номер (серийный номер)
            - изготовитель (название организации)
            - адрес, телефон, email, сайт изготовителя
            - дату изготовления / выпуска
            - гарантийный срок
            - срок службы
            - технические характеристики (напряжение, ток, мощность, масса, габариты, температура и тд)
            - стандарты и сертификаты (ГОСТ, ТУ)
            - обозначение документа (например БНРД.434400.046ПС)
            
            Пример структуры:
            {
              "наименование": "...",
              "модель": "...",
              "заводской_номер": "...",
              "изготовитель": "...",
              "гарантийный_срок": "...","напряжение": "...",
              ... (все что нашёл)
            }
            """,
            
            "cabinet_list": base + """
            Это перечень документации шкафа.
            Ищи:
            - название шкафа
            - код или обозначение шкафа
            - заводской номер шкафа
            - таблицу с перечнем документов (номер, наименование, заводской номер, страниц, сертификат)
            
            Пример структуры:
            {
              "наименование_шкафа": "Шкаф общего назначения №10",
              "код_шкафа": "G4-32Y31-JP-CA-1014",
              "заводской_номер": "20430",
              "состав": [
                {
                  "номер": 1,
                  "наименование": "Контроллер МФК 1500. Паспорт",
                  "заводской_номер": "042401184530",
                  "страниц": 7,
                  "сертификатов": 1
                }
              ]
            }
            """,
            
            "manual": base + """
            Это руководство по эксплуатации.
            Ищи только:
            - наименование устройства
            - изготовитель и его контакты
            - технические характеристики (из раздела "Технические характеристики")
            - гарантийный срок
            - срок службы
            Не включай инструкции по установке и обслуживанию.
            """,
            
            "warranty": base + """
            Это гарантийный талон.
            Ищи:
            - наименование оборудования
            - модель
            - дату приобретения
            - заводской номер
            - гарантийный срок
            - продавца
            """,
            
            "acceptance": base + """
            Это свидетельство о приёмке или акт.
            Ищи:
            - наименование изделия
            - заводской номер
            - дату приёмки
            - ответственного за приёмку
            - результат приёмки
            """
        }
        
        return prompts.get(doc_type, prompts["passport"])
    
    # ─────────────────────────────────────────────────────
    # ШАГ 4: Верификация
    # ─────────────────────────────────────────────────────
    
    def _verify(self, first_page: Image, merged_data: dict) -> dict:
        """
        Второй проход — смотрим на первую страницу
        и проверяем что главные поля заполнены правильно
        """
        
        # Что у нас уже есть
        already_found = json.dumps(merged_data, ensure_ascii=False, indent=2)
        
        prompt = f"""
        Посмотри на эту страницу документа.
        
        Система уже извлекла следующие данные:
        {already_found}
        
        Твоя задача:
        1. Проверь правильность каждого поля
        2. Исправь если видишь ошибку
        3. Добавь поля которые пропустили
        
        Верни исправленный и дополненный JSON.
        Верни ТОЛЬКО валидный JSON. Без пояснений.
        """
        
        response = self._call_model(first_page, prompt, max_tokens=3000)
        verified = self._parse_json(response)
        
        # Если верификация вернула пустой результат — 
        # оставляем оригинал
        return verified if verified else merged_data
    
    # ─────────────────────────────────────────────────────
    # Вспомогательные методы
    # ─────────────────────────────────────────────────────
    
    def _call_model(self, image: Image, prompt: str, max_tokens: int) -> str:
        image_b64 = self._to_base64(image)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt}
                    ]
                }
            ],
            temperature=0.0,  # максимальная детерминированность
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def _to_base64(self, image: Image) -> str:
        # Оптимальный размер для точности
        # Слишком маленький → теряем детали
        # Слишком большой → медленно
        max_size = 2000
        if max(image.size) > max_size:
            image = image.copy()
            image.thumbnail((max_size, max_size), Image.LANCZOS)
        
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=95)  # высокое качество
        return base64.b64encode(buffer.getvalue()).decode()
    
    def _parse_json(self, content: str) -> dict:
        text = re.sub(r'^```(?:json)?\s*\n?', '', content.strip())
        text = re.sub(r'\n?\s*```$', '', text).strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    pass
        return {}
    
    def _merge(self, results: list[dict]) -> dict:
        merged = {}
        for result in results:
            for key, value in result.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, list) and isinstance(merged[key], list):
                    merged[key].extend(value)
                elif isinstance(value, str) and isinstance(merged[key], str):
                    if len(value) > len(merged[key]):
                        merged[key] = value
        return merged
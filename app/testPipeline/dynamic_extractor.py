# dynamic_extractor.py

from typing import Dict, Any, List, Optional
from app.testPipeline.universal_pasport_schema import UniversalPassport
import re

class DynamicExtractor:
    """Экстрактор, который адаптируется к типу оборудования"""
    
    def __init__(self):
        # Словарь паттернов для ВСЕХ возможных полей
        self.all_patterns = self._init_all_patterns()
        
        # Типы оборудования и их специфичные поля
        self.equipment_types = {
            'розетка': ['nominal_voltage', 'nominal_current', 'frequency', 'protection_degree'],
            'пресс': ['nominal_force', 'stroke_length', 'table_dimensions', 'weight'],
            'двигатель': ['power', 'rpm', 'voltage', 'efficiency'],
            'трансформатор': ['power', 'voltage_primary', 'voltage_secondary', 'frequency'],
        }
    
    def _init_all_patterns(self) -> Dict[str, List[str]]:
        """Инициализация ВСЕХ возможных паттернов"""
        return {
            # Общие
            'product_name': [
                r'((?:Розетка|Пресс|Двигатель|Трансформатор)[^\n]{10,100})',
            ],
            'model': [
                r'[Мм]одель[:\s]+([A-Z0-9-]+)',
                r'МОДЕЛЬ\s+([A-Z0-9]+)',
            ],
            'passport_number': [
                r'([А-Я]{2,6}\.\d{3,6}\.\d{2,6}[А-Я]{2})',
            ],
            'factory_number': [
                r'[Зз]аводской\s+№\s*(\d+)',
                r'№\s*(\d+)',
            ],
            
            # Электрические параметры
            'nominal_voltage': [
                r'[Нн]оминальное\s+напряжение[^\d]+(\d+)\s*В',
                r'напряжением\s+(?:до\s+)?(\d+)\s*В',
            ],
            'nominal_current': [
                r'[Нн]оминальный\s+ток[^\d]+(\d+)\s*А',
                r'током\s+до\s+(\d+)\s*А',
            ],
            'frequency': [
                r'[Чч]астота[^\d]+(\d+)\s*Гц',
            ],
            'protection_degree': [
                r'([IР]{1,2}\d{2})',
            ],
            
            # Механические параметры
            'nominal_force': [
                r'усилием\s+(\d+\s*тс)',
                r'([0-9]+)\s*тс',
            ],
            'weight': [
                r'[Вв]ес[^\d]+(\d+(?:\.\d+)?)\s*кг',
                r'[Мм]асса[^\d]+(\d+(?:\.\d+)?)\s*кг',
            ],
            
            # Производитель
            'manufacturer_name': [
                r'[Ии]зготовитель:\s*(.+?)(?:\n|Адрес)',
                r'(?:АО|ООО|ЗАО)\s+[«"]?(.+?)[»"]?',
            ],
            'manufacturer_address': [
                r'[Аа]дрес:\s*(.+?)(?:\n|Телефон)',
            ],
            
            # Даты
            'manufacture_date': [
                r'[Дд]ата\s+изготовления[:\s]+(\d{2}\.\d{2}\.\d{4})',
            ],
            
            # Сроки
            'warranty_period': [
                r'[Гг]арантийный\s+срок[^\d]+(\d+\s+(?:лет|года|год))',
            ],
            'service_life': [
                r'[Сс]рок\s+службы[^\d]+(\d+\s+лет)',
            ],
            
            # Регуляторные документы
            'tu_number': [
                r'ТУ\s*([0-9-]+)',
            ],
            'gost_numbers': [
                r'ГОСТ\s+(?:IEC\s+)?(\d+(?:-\d+)?)',
            ],
        }
    
    def detect_equipment_type(self, text: str) -> str:
        """Определить тип оборудования"""
        text_lower = text.lower()
        
        if 'розетка' in text_lower:
            return 'розетка'
        elif 'пресс' in text_lower:
            return 'пресс'
        elif 'двигатель' in text_lower or 'мотор' in text_lower:
            return 'двигатель'
        elif 'трансформатор' in text_lower:
            return 'трансформатор'
        else:
            return 'unknown'
    
    def extract(self, text: str) -> UniversalPassport:
        """Динамическое извлечение"""
        
        passport = UniversalPassport()
        
        # 1. Определяем тип оборудования
        equipment_type = self.detect_equipment_type(text)
        passport.equipment_type = equipment_type
        
        # 2. Извлекаем общие поля
        passport.product_name = self._extract_field(text, 'product_name')
        passport.model = self._extract_field(text, 'model')
        passport.passport_number = self._extract_field(text, 'passport_number')
        
        # 3. Производитель
        passport.manufacturer = {
            'name': self._extract_field(text, 'manufacturer_name'),
            'address': self._extract_field(text, 'manufacturer_address'),
        }
        
        # 4. Идентификация
        passport.identification = {
            'factory_number': self._extract_field(text, 'factory_number'),
        }
        
        # 5. Даты
        passport.dates = {
            'manufacture_date': self._extract_field(text, 'manufacture_date'),
        }
        
        # 6. ДИНАМИЧЕСКИЕ технические характеристики
        passport.technical_specs = self._extract_technical_specs(text, equipment_type)
        
        # 7. Регуляторные документы
        passport.regulatory_docs = {
            'tu_number': self._extract_field(text, 'tu_number'),
            'gost_numbers': self._extract_all(text, 'gost_numbers'),
        }
        
        # 8. Жизненный цикл
        passport.lifecycle = {
            'warranty_period': self._extract_field(text, 'warranty_period'),
            'service_life': self._extract_field(text, 'service_life'),
        }
        
        return passport
    
    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Извлечь одно поле"""
        patterns = self.all_patterns.get(field_name, [])
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_all(self, text: str, field_name: str) -> List[str]:
        """Извлечь все вхождения"""
        patterns = self.all_patterns.get(field_name, [])
        results = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            results.extend(matches)
        return list(set(results))  # Убираем дубликаты
    
    def _extract_technical_specs(self, text: str, equipment_type: str) -> Dict[str, Any]:
        """Извлечь технические характеристики в зависимости от типа"""
        specs = {}
        
        # Определяем, какие поля искать
        relevant_fields = self.equipment_types.get(equipment_type, [])
        
        # Извлекаем только релевантные поля
        for field in relevant_fields:
            value = self._extract_field(text, field)
            if value:
                specs[field] = value
        
        # Также извлекаем ВСЕ числовые характеристики (на всякий случай)
        specs.update(self._extract_all_numeric_params(text))
        
        return specs
    
    def _extract_all_numeric_params(self, text: str) -> Dict[str, str]:
        """Извлечь все параметры вида 'Название: число единица'"""
        pattern = r'([А-Яа-я\s]+)[:,-]\s*(\d+(?:[.,]\d+)?)\s*([А-Яа-я]+)?'
        matches = re.findall(pattern, text)
        
        params = {}
        for name, value, unit in matches:
            name = name.strip()
            if len(name) > 3 and len(name) < 50:  # Фильтруем шум
                full_value = f"{value} {unit}".strip() if unit else value
                params[name.lower().replace(' ', '_')] = full_value
        
        return params
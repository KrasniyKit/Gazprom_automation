# improved_patterns.py

import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PassportData:
    """Структура данных паспорта"""
    doc_type: str = "equipment_passport"
    passport_number: Optional[str] = None
    product_name: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturer_address: Optional[str] = None
    
    # Технические характеристики
    nominal_voltage: Optional[str] = None
    nominal_current: Optional[str] = None
    frequency: Optional[str] = None
    protection_degree: Optional[str] = None
    climate_type: Optional[str] = None
    
    # Номера документов
    tu_number: Optional[str] = None
    gost_numbers: List[str] = None
    
    # Сроки
    warranty_period: Optional[str] = None
    service_life: Optional[str] = None
    
    # Прочее
    issue_date: Optional[str] = None
    factory_number: Optional[str] = None
    

class ImprovedExtractor:
    """Улучшенный экстрактор для паспортов оборудования"""
    
    def __init__(self):
        # Комплексные паттерны
        self.patterns = {
            # Номер паспорта (код документа)
            'passport_number': [
                r'Руководство\s+по\s+эксплуатации\s+([А-Я]{2,6}\.\d{3,6}\.\d{2,6}[А-Я]{2})',
                r'([А-Я]{2,6}\.\d{3,6}\.\d{2,6}[А-Я]{2})',
            ],
            
            # Название продукта (более точное)
            'product_name': [
                r'((?:Розетка|Автомат|Выключатель|Контактор|Реле)\s+OptiDin\s+[А-Я0-9/-]+(?:-[А-ЯA-Z0-9]+)*)',
                r'(OptiDin\s+[А-Я]{1,3}\d{1,2}/\d{1,2}-\d{3}-[А-Я](?:-[А-Я0-9]+)?)',
            ],
            
            # ТУ (Технические условия)
            'tu_number': [
                r'ТУ\s*([0-9-]+)',
                r'изготавливаются\s+по\s+ТУ\s*([0-9-]+)',
            ],
            
            # ГОСТ
            'gost_numbers': [
                r'ГОСТ\s+(?:IEC\s+)?(\d+(?:-\d+)?)',
            ],
            
            # Производитель
            'manufacturer': [
                r'Изготовитель:\s*(.+?)(?:Адрес|$)',
                r'АО\s+«(.+?)»',
                r'Акционерное\s+общество\s+(.+?)(?:\(|Адрес)',
            ],
            
            # Адрес
            'manufacturer_address': [
                r'Адрес:\s*(.+?)(?:Телефон|$)',
                r'Россия,\s+\d{6},\s+(.+?)(?:\n|Телефон)',
            ],
            
            # Технические характеристики
            'nominal_voltage': [
                r'Номинальное\s+напряжение[,\s]+[A-Za-z]+[,\s]+В\s+(\d+)',
                r'напряжением\s+до\s+(\d+)\s+В',
            ],
            
            'nominal_current': [
                r'Номинальный\s+ток[,\s]+[A-Za-z]+[,\s]+A\s+(\d+)',
                r'номинальным\s+током\s+до\s+(\d+)\s+А',
            ],
            
            'frequency': [
                r'Частота\s+тока[,\s]+Гц\s+(\d+)',
                r'частоты\s+(\d+)\s+Гц',
            ],
            
            'protection_degree': [
                r'(?:степени|степенью)\s+защиты\s+(?:не\s+ниже\s+)?([IР]{1,2}\d{2})',
                r'Степень\s+защиты[^\n]+([IР]{1,2}\d{2})',
            ],
            
            'climate_type': [
                r'Климатическое\s+исполнение[^\n]+([А-Я]{2,4}\d)',
                r'([А-Я]{2,4}\d)\s+по\s+ГОСТ\s+15150',
            ],
            
            # Сроки
            'warranty_period': [
                r'Гарантийный\s+срок\s+составляет\s+(\d+\s+(?:лет|года|год))',
            ],
            
            'service_life': [
                r'Срок\s+службы[^\n]+не\s+менее\s+(\d+\s+лет)',
            ],
            
            # Дата (если есть)
            'issue_date': [
                r'Дата\s+изготовления[:\s]+(\d{2}\.\d{2}\.\d{4})',
                r'(\d{2}\.\d{2}\.\d{4})',
            ],
            
            'factory_number': [
                r'(?:Серийный|Заводской)\s+номер[:\s]+([А-Я0-9-]+)',
                r'№\s+([А-Я0-9-]+)',
            ],
        }
    
    def extract(self, text: str) -> PassportData:
        """Извлечение всех данных"""
        data = PassportData()
        data.gost_numbers = []
        
        # Извлекаем по всем паттернам
        for field, patterns in self.patterns.items():
            if field == 'gost_numbers':
                # Для ГОСТ - находим все вхождения
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
                    data.gost_numbers.extend(matches)
            else:
                # Для остальных - первое совпадение
                value = self._find_first_match(text, patterns)
                if value:
                    setattr(data, field, value.strip())
        
        # Постобработка
        data = self._post_process(data, text)
        
        return data
    
    def _find_first_match(self, text: str, patterns: List[str]) -> Optional[str]:
        """Найти первое совпадение"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        return None
    
    def _post_process(self, data: PassportData, text: str) -> PassportData:
        """Постобработка и очистка данных"""
        
        # Очистка названия продукта от мусора
        if data.product_name:
            # Убираем лишние символы в конце
            data.product_name = re.sub(r'\s+[рp]\s*\|?\s*\[?\s*$', '', data.product_name)
            data.product_name = data.product_name.strip()
        
        # Нормализация производителя
        if data.manufacturer:
            # Убираем "Изготовитель:" если попало
            data.manufacturer = re.sub(r'^Изготовитель:\s*', '', data.manufacturer)
            data.manufacturer = data.manufacturer.strip()
        
        # Добавляем единицы измерения
        if data.nominal_voltage:
            data.nominal_voltage = f"{data.nominal_voltage} В"
        
        if data.nominal_current:
            data.nominal_current = f"{data.nominal_current} А"
        
        if data.frequency:
            data.frequency = f"{data.frequency} Гц"
        
        # Проверка на наличие заводского номера
        if not data.factory_number:
            # Проверяем фразы типа "указан на упаковке"
            if re.search(r'(?:Дата|номер)[^\n]*указан[^\n]*на\s+упаковке', text, re.IGNORECASE):
                data.factory_number = "НЕ УКАЗАН (см. упаковку)"
        
        if not data.issue_date:
            if re.search(r'Дата\s+изготовления\s+указана\s+на\s+упаковке', text, re.IGNORECASE):
                data.issue_date = "НЕ УКАЗАНА (см. упаковку)"
        
        return data
    
    def to_dict(self, data: PassportData) -> Dict:
        """Конвертация в словарь"""
        return {
            "doc_type": data.doc_type,
            "passport_number": data.passport_number,
            "product_name": data.product_name,
            "manufacturer": {
                "name": data.manufacturer,
                "address": data.manufacturer_address,
            },
            "technical_specs": {
                "nominal_voltage": data.nominal_voltage,
                "nominal_current": data.nominal_current,
                "frequency": data.frequency,
                "protection_degree": data.protection_degree,
                "climate_type": data.climate_type,
            },
            "regulatory_docs": {
                "tu_number": data.tu_number,
                "gost_numbers": data.gost_numbers,
            },
            "lifecycle": {
                "warranty_period": data.warranty_period,
                "service_life": data.service_life,
            },
            "identification": {
                "issue_date": data.issue_date,
                "factory_number": data.factory_number,
            }
        }
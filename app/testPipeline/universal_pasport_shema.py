# universal_passport_schema.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class UniversalPassport:
    """Универсальная структура паспорта оборудования"""
    
    # ===== ОБЯЗАТЕЛЬНЫЕ ПОЛЯ (есть у всех) =====
    doc_type: str = "equipment_passport"  # Тип документа
    equipment_type: str = None  # "розетка", "пресс", "двигатель" и т.д.
    
    # Базовая идентификация
    product_name: Optional[str] = None
    model: Optional[str] = None
    passport_number: Optional[str] = None
    
    # Производитель
    manufacturer: Optional[Dict[str, str]] = field(default_factory=dict)
    # {"name": "...", "address": "...", "phone": "..."}
    
    # Идентификационные номера
    identification: Optional[Dict[str, str]] = field(default_factory=dict)
    # {"serial_number": "...", "factory_number": "...", "inventory_number": "..."}
    
    # Даты
    dates: Optional[Dict[str, str]] = field(default_factory=dict)
    # {"manufacture_date": "...", "issue_date": "...", "acceptance_date": "..."}
    
    # ===== ГИБКИЕ ПОЛЯ (зависят от типа) =====
    
    # Технические характеристики (ДИНАМИЧЕСКИЕ!)
    technical_specs: Dict[str, Any] = field(default_factory=dict)
    
    # Регуляторные документы
    regulatory_docs: Dict[str, Any] = field(default_factory=dict)
    
    # Жизненный цикл
    lifecycle: Dict[str, Any] = field(default_factory=dict)
    
    # Дополнительные параметры (всё что не вошло выше)
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    # ===== МЕТАДАННЫЕ =====
    source: Dict[str, Any] = field(default_factory=dict)
    extraction_quality: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Конвертация в словарь"""
        return {
            "doc_type": self.doc_type,
            "equipment_type": self.equipment_type,
            "product_name": self.product_name,
            "model": self.model,
            "passport_number": self.passport_number,
            "manufacturer": self.manufacturer,
            "identification": self.identification,
            "dates": self.dates,
            "technical_specs": self.technical_specs,
            "regulatory_docs": self.regulatory_docs,
            "lifecycle": self.lifecycle,
            "additional_data": self.additional_data,
            "source": self.source,
            "extraction_quality": self.extraction_quality,
            "processed_at": datetime.now().isoformat()
        }
    
    def to_json(self, filepath: str = None) -> str:
        """Экспорт в JSON"""
        data = self.to_dict()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
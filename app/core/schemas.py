from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ItemSchema(BaseModel):
    line_number: Optional[int] = None
    name: str
    passport_number: Optional[str] = None
    factory_number: Optional[str] = None
    pages_count: Optional[int] = None
    certificate_count: Optional[int] = None


class ItemsListSchema(BaseModel):
    list_type: str = "array"
    min_items: int = 1
    items: Optional[List[ItemSchema]] = None


class SourceSchema(BaseModel):
    file_name: str
    page_count: int
    ocr_engine: Optional[str] = None
    ocr_confidence: Optional[float] = None


class PassportResponseSchema(BaseModel):
    doc_type: str = "equipment_passport"
    
    equipment_name: str
    purpose: Optional[str] = None
    technical_specs: Optional[str] = None
    
    manufacturer: str
    normative_docs: Optional[str] = None
    passport_number: Optional[str] = None
    issue_date: Optional[datetime] = None
    
    completeness: Optional[str] = None
    service_life: Optional[str] = None
    warranty: Optional[str] = None
    
    items: ItemsListSchema
    source: SourceSchema
    notes: Optional[str] = None
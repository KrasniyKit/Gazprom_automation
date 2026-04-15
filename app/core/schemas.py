from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    EQUIPMENT_PASSPORT = "equipment_passport"


class BarcodeType(str, Enum):
    CODE39 = "Code39"
    CODE128 = "Code128"
    EAN13 = "EAN-13"


class BarcodeSchema(BaseModel):
    type: BarcodeType
    value: str = Field(min_length=1)


class ItemSchema(BaseModel):
    """
    Scheme of extracted passport fields
    """

    line_number: Optional[int] = None
    name: str = Field(min_length=1)
    passport_number: str = Field(min_length=1)
    factory_number: Optional[str] = Field(min_length=1)
    pages_count: Optional[int] = None
    certificate_count: Optional[int] = None


class ItemsListSchema(BaseModel):
    """
    Scheme of a list of extracted fields
    """

    type: str = "array"
    min_items: int = Field(1)
    items: list[ItemSchema]


class SourceSchema(BaseModel):
    file_name: str = Field(min_length=1)
    page_count: int = Field(ge=1)
    ocr_engine: Optional[str]
    ocr_confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)


class PassportResponseSchema(BaseModel):
    doc_type: DocumentType = DocumentType.EQUIPMENT_PASSPORT
    passport_number: str = Field(
        min_length=1, description="Passport number or identifier visible in document"
    )
    issue_date: Optional[datetime] = None
    manufacturer: str = Field(min_length=1)
    items: ItemsListSchema
    source: SourceSchema
    notes: Optional[str] = None

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


UncertainField = Literal[
    "equipment_name",
    "purpose",
    "technical_specs",
    "manufacturer",
    "normative_docs",
    "passport_number",
    "issue_date",
    "completeness",
    "service_life",
    "warranty",
]


class SourceSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_name: str
    page_count: int = 0
    ocr_engine: str = ""
    ocr_confidence: Optional[float] = None

class PassportResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_type: Literal["equipment_passport"] = "equipment_passport"

    equipment_name: str
    purpose: str = ""
    technical_specs: str = ""

    manufacturer: str
    normative_docs: str = ""
    passport_number: str = ""
    issue_date: Optional[datetime] = None

    completeness: str = ""
    service_life: str = ""
    warranty: str = ""

    uncertain_fields: List[UncertainField] = Field(default_factory=list)

    source: SourceSchema
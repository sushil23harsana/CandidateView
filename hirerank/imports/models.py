from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class CandidateImportResult:
    row_number: int
    status: str
    candidate_id: Optional[str] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class CandidateImportJob:
    import_id: str
    owner_id: str
    job_id: str
    status: str
    headers: List[str]
    mapping: Dict[str, str]
    total_rows: int
    processed_rows: int
    success_count: int
    failure_count: int
    results: List[CandidateImportResult] = field(default_factory=list)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CandidateImportPreview:
    headers: List[str]
    rows: List[Dict[str, str]]

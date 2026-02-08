from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List

from hirerank.dashboard.models import CandidateApplication


class ApplicationRepository:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, application: CandidateApplication) -> None:
        data = self._load()
        payload = asdict(application)
        payload["created_at"] = application.created_at.isoformat()
        data.append(payload)
        self._write(data)

    def list_by_job(self, owner_id: str, job_id: str) -> List[CandidateApplication]:
        data = self._load()
        applications: List[CandidateApplication] = []
        for payload in data:
            if not isinstance(payload, dict):
                continue
            if str(payload.get("owner_id")) != owner_id:
                continue
            if str(payload.get("job_id")) != job_id:
                continue
            created_at = payload.get("created_at")
            applications.append(
                CandidateApplication(
                    application_id=str(payload.get("application_id", "")),
                    candidate_id=str(payload.get("candidate_id", "")),
                    job_id=str(payload.get("job_id", "")),
                    owner_id=str(payload.get("owner_id", "")),
                    status=str(payload.get("status", "")),
                    skills=list(payload.get("skills") or []),
                    created_at=datetime.fromisoformat(created_at) if created_at else datetime.utcnow(),
                )
            )
        return applications

    def _load(self) -> List[object]:
        if not self.storage_path.exists():
            return []
        with self.storage_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data: List[object]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

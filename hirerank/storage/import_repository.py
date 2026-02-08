from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from hirerank.imports.models import CandidateImportJob, CandidateImportResult


class CandidateImportRepository:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, job: CandidateImportJob) -> None:
        data = self._load()
        data.append(self._to_payload(job))
        self._write(data)

    def update(self, job: CandidateImportJob) -> None:
        data = self._load()
        updated = False
        for idx, payload in enumerate(data):
            if isinstance(payload, dict) and payload.get("import_id") == job.import_id:
                data[idx] = self._to_payload(job)
                updated = True
                break
        if not updated:
            data.append(self._to_payload(job))
        self._write(data)

    def get(self, owner_id: str, job_id: str, import_id: str) -> Optional[CandidateImportJob]:
        data = self._load()
        for payload in data:
            if not isinstance(payload, dict):
                continue
            if str(payload.get("import_id")) != import_id:
                continue
            if str(payload.get("owner_id")) != owner_id:
                continue
            if str(payload.get("job_id")) != job_id:
                continue
            return self._from_payload(payload)
        return None

    def list_by_job(self, owner_id: str, job_id: str) -> List[CandidateImportJob]:
        data = self._load()
        jobs: List[CandidateImportJob] = []
        for payload in data:
            if not isinstance(payload, dict):
                continue
            if str(payload.get("owner_id")) != owner_id:
                continue
            if str(payload.get("job_id")) != job_id:
                continue
            jobs.append(self._from_payload(payload))
        return jobs

    def _from_payload(self, payload: dict) -> CandidateImportJob:
        results_data = payload.get("results") or []
        results: List[CandidateImportResult] = []
        for result in results_data:
            if not isinstance(result, dict):
                continue
            results.append(
                CandidateImportResult(
                    row_number=int(result.get("row_number", 0)),
                    status=str(result.get("status", "")),
                    candidate_id=result.get("candidate_id"),
                    errors=list(result.get("errors") or []),
                )
            )
        created_at = payload.get("created_at")
        updated_at = payload.get("updated_at")
        return CandidateImportJob(
            import_id=str(payload.get("import_id", "")),
            owner_id=str(payload.get("owner_id", "")),
            job_id=str(payload.get("job_id", "")),
            status=str(payload.get("status", "")),
            headers=list(payload.get("headers") or []),
            mapping=dict(payload.get("mapping") or {}),
            total_rows=int(payload.get("total_rows", 0)),
            processed_rows=int(payload.get("processed_rows", 0)),
            success_count=int(payload.get("success_count", 0)),
            failure_count=int(payload.get("failure_count", 0)),
            results=results,
            error_message=payload.get("error_message"),
            created_at=datetime.fromisoformat(created_at) if created_at else datetime.utcnow(),
            updated_at=datetime.fromisoformat(updated_at) if updated_at else datetime.utcnow(),
        )

    def _to_payload(self, job: CandidateImportJob) -> dict:
        payload = asdict(job)
        payload["created_at"] = job.created_at.isoformat()
        payload["updated_at"] = job.updated_at.isoformat()
        return payload

    def _load(self) -> List[object]:
        if not self.storage_path.exists():
            return []
        with self.storage_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data: List[object]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

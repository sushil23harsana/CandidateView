from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from hirerank.scoring.models import ScoreBreakdown, ScoreComponent, ScoreResult


class ScoringRepository:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, result: ScoreResult, owner_id: Optional[str] = None) -> None:
        data = self._load()
        resolved_owner = (owner_id or result.owner_id or "").strip() or None
        if resolved_owner:
            job_key = f"{resolved_owner}:{result.job_id}:{result.candidate_id}"
        else:
            job_key = f"{result.job_id}:{result.candidate_id}"
        if resolved_owner:
            result = ScoreResult(
                candidate_id=result.candidate_id,
                job_id=result.job_id,
                total_score=result.total_score,
                breakdown=result.breakdown,
                explanation=result.explanation,
                created_at=result.created_at,
                owner_id=resolved_owner,
            )
        data[job_key] = result.as_dict()
        self._write(data)

    def list_by_job(self, owner_id: str, job_id: str) -> Dict[str, ScoreResult]:
        data = self._load()
        results: Dict[str, ScoreResult] = {}
        prefix = f"{owner_id}:{job_id}:"
        for key, payload in data.items():
            if not key.startswith(prefix):
                continue
            if not isinstance(payload, dict):
                continue
            payload_owner = str(payload.get("owner_id", "")).strip()
            if payload_owner and payload_owner != owner_id:
                continue
            candidate_id = str(payload.get("candidate_id", "")).strip()
            if not candidate_id:
                continue
            breakdown_payload = payload.get("breakdown") or {}
            components = []
            if isinstance(breakdown_payload, dict):
                for category, details in breakdown_payload.items():
                    if not isinstance(details, dict):
                        continue
                    score_value = details.get("score")
                    score = float(score_value) if isinstance(score_value, (int, float)) else None
                    components.append(
                        ScoreComponent(
                            category=str(category),
                            score=score,
                            weight=float(details.get("weight", 0.0)),
                            weighted_score=float(details.get("weighted_score", 0.0)),
                            explanation=str(details.get("explanation", "")),
                        )
                    )
            results[candidate_id] = ScoreResult(
                candidate_id=candidate_id,
                job_id=str(payload.get("job_id", job_id)),
                total_score=float(payload.get("total_score", 0.0)),
                breakdown=ScoreBreakdown(components=components),
                explanation=str(payload.get("explanation", "")),
                created_at=datetime.fromisoformat(payload.get("created_at"))
                if payload.get("created_at")
                else datetime.utcnow(),
                owner_id=payload_owner or owner_id,
            )
        return results

    def _load(self) -> Dict[str, object]:
        if not self.storage_path.exists():
            return {}
        with self.storage_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data: Dict[str, object]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

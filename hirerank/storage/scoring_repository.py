from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from hirerank.scoring.models import ScoreResult


class ScoringRepository:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, result: ScoreResult) -> None:
        data = self._load()
        job_key = f"{result.job_id}:{result.candidate_id}"
        data[job_key] = result.as_dict()
        self._write(data)

    def _load(self) -> Dict[str, object]:
        if not self.storage_path.exists():
            return {}
        with self.storage_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data: Dict[str, object]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

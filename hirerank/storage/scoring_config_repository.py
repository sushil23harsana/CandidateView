from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from hirerank.scoring.config import CategoryWeights, ResumeSubWeights, ScoringConfig


class ScoringConfigRepository:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, config: ScoringConfig) -> None:
        data = self._load()
        data[config.job_id] = {
            "job_id": config.job_id,
            "github_required": config.github_required,
            "category_weights": config.category_weights.as_percentages(),
            "resume_subweights": {
                "required_skills": config.resume_subweights.required_skills,
                "experience_fit": config.resume_subweights.experience_fit,
                "nice_to_have": config.resume_subweights.nice_to_have,
            },
        }
        self._write(data)

    def get(self, job_id: str) -> ScoringConfig:
        data = self._load()
        config_data = data.get(job_id)
        if not config_data:
            return ScoringConfig(job_id=job_id)
        weights = config_data.get("category_weights", {})
        return ScoringConfig(
            job_id=job_id,
            github_required=config_data.get("github_required", False),
            category_weights=CategoryWeights(
                resume_skills=weights.get("resume_skills", 25) / 100,
                github_code_quality=weights.get("github_code_quality", 30) / 100,
                project_originality=weights.get("project_originality", 20) / 100,
                documentation_quality=weights.get("documentation_quality", 10) / 100,
                engineering_practices=weights.get("engineering_practices", 15) / 100,
            ),
            resume_subweights=ResumeSubWeights(
                required_skills=config_data.get("resume_subweights", {}).get("required_skills", 0.6),
                experience_fit=config_data.get("resume_subweights", {}).get("experience_fit", 0.2),
                nice_to_have=config_data.get("resume_subweights", {}).get("nice_to_have", 0.2),
            ),
        )

    def _load(self) -> Dict[str, object]:
        if not self.storage_path.exists():
            return {}
        with self.storage_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data: Dict[str, object]) -> None:
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

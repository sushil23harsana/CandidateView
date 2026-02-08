from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ScoreComponent:
    category: str
    score: Optional[float]
    weight: float
    weighted_score: float
    explanation: str


@dataclass
class ScoreBreakdown:
    components: List[ScoreComponent] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Dict[str, float | str | None]]:
        return {
            component.category: {
                "score": component.score,
                "weight": component.weight,
                "weighted_score": component.weighted_score,
                "explanation": component.explanation,
            }
            for component in self.components
        }


@dataclass
class ScoreResult:
    candidate_id: str
    job_id: str
    total_score: float
    breakdown: ScoreBreakdown
    explanation: str
    owner_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def as_dict(self) -> Dict[str, object]:
        payload = {
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "total_score": self.total_score,
            "breakdown": self.breakdown.as_dict(),
            "explanation": self.explanation,
            "created_at": self.created_at.isoformat(),
        }
        if self.owner_id:
            payload["owner_id"] = self.owner_id
        return payload

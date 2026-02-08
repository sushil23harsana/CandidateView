from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class CandidateApplication:
    application_id: str
    candidate_id: str
    job_id: str
    owner_id: str
    status: str
    skills: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CandidateDashboardEntry:
    application_id: str
    candidate_id: str
    status: str
    skills: List[str]
    total_score: Optional[float]
    breakdown: Dict[str, Dict[str, float | str | None]]
    explanation_summary: str
    explanation: str
    score_created_at: Optional[str]


@dataclass
class ScoreDistributionBucket:
    label: str
    min_score: float
    max_score: float
    count: int


@dataclass
class SkillMatchCount:
    skill: str
    count: int


@dataclass
class JobInsights:
    job_id: str
    total_applications: int
    scored_applications: int
    unscored_applications: int
    score_distribution: List[ScoreDistributionBucket]
    top_skill_matches: List[SkillMatchCount]

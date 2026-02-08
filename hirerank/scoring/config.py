from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class CategoryWeights:
    resume_skills: float = 0.25
    github_code_quality: float = 0.30
    project_originality: float = 0.20
    documentation_quality: float = 0.10
    engineering_practices: float = 0.15

    def normalized(self) -> "CategoryWeights":
        total = (
            self.resume_skills
            + self.github_code_quality
            + self.project_originality
            + self.documentation_quality
            + self.engineering_practices
        )
        if total <= 0:
            raise ValueError("Total category weight must be greater than zero.")
        return CategoryWeights(
            resume_skills=self.resume_skills / total,
            github_code_quality=self.github_code_quality / total,
            project_originality=self.project_originality / total,
            documentation_quality=self.documentation_quality / total,
            engineering_practices=self.engineering_practices / total,
        )

    def as_percentages(self) -> Dict[str, float]:
        normalized = self.normalized()
        return {
            "resume_skills": round(normalized.resume_skills * 100, 2),
            "github_code_quality": round(normalized.github_code_quality * 100, 2),
            "project_originality": round(normalized.project_originality * 100, 2),
            "documentation_quality": round(normalized.documentation_quality * 100, 2),
            "engineering_practices": round(normalized.engineering_practices * 100, 2),
        }


@dataclass(frozen=True)
class ResumeSubWeights:
    required_skills: float = 0.60
    experience_fit: float = 0.20
    nice_to_have: float = 0.20

    def normalized(self) -> "ResumeSubWeights":
        total = self.required_skills + self.experience_fit + self.nice_to_have
        if total <= 0:
            raise ValueError("Total resume sub-weights must be greater than zero.")
        return ResumeSubWeights(
            required_skills=self.required_skills / total,
            experience_fit=self.experience_fit / total,
            nice_to_have=self.nice_to_have / total,
        )


@dataclass(frozen=True)
class ScoringConfig:
    job_id: str
    category_weights: CategoryWeights = field(default_factory=CategoryWeights)
    resume_subweights: ResumeSubWeights = field(default_factory=ResumeSubWeights)
    github_required: bool = False

    def normalized(self) -> "ScoringConfig":
        return ScoringConfig(
            job_id=self.job_id,
            category_weights=self.category_weights.normalized(),
            resume_subweights=self.resume_subweights.normalized(),
            github_required=self.github_required,
        )

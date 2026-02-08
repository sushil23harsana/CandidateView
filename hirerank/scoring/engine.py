from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from hirerank.scoring.config import ScoringConfig
from hirerank.scoring.models import ScoreBreakdown, ScoreComponent, ScoreResult


@dataclass
class ResumeAnalysis:
    required_skills_matched: int
    required_skills_total: int
    nice_to_have_matched: int
    nice_to_have_total: int
    experience_years: float
    required_experience_years: float


@dataclass
class GitHubAnalysis:
    code_quality_score: float
    documentation_score: float
    engineering_practices_score: float
    projects: List[Dict[str, object]]


@dataclass
class ProjectAnalysis:
    originality_score: float
    is_tutorial: bool
    tutorial_indicators: List[str]
    green_flags: List[str]


def _clamp(score: float) -> float:
    return max(0.0, min(100.0, score))


def _safe_ratio(numerator: float, denominator: float) -> Optional[float]:
    if denominator <= 0:
        return None
    return numerator / denominator


def _normalize_available(weights: Dict[str, float], available: Iterable[str]) -> Dict[str, float]:
    available_weights = {key: weights[key] for key in available}
    total = sum(available_weights.values())
    if total == 0:
        return {key: 0 for key in available_weights}
    return {key: value / total for key, value in available_weights.items()}


def _combine_explanations(lines: Iterable[str]) -> str:
    return "\n".join(line for line in lines if line)


def _resume_score(resume: ResumeAnalysis, config: ScoringConfig) -> Tuple[float, str]:
    subweights = config.resume_subweights.normalized()
    required_ratio = _safe_ratio(resume.required_skills_matched, resume.required_skills_total)
    nice_ratio = _safe_ratio(resume.nice_to_have_matched, resume.nice_to_have_total)

    required_score = _clamp((required_ratio or 0.0) * 100)
    nice_score = _clamp((nice_ratio or 0.0) * 100) if nice_ratio is not None else 50.0

    if resume.required_experience_years <= 0:
        experience_score = 100.0
    else:
        experience_score = _clamp((resume.experience_years / resume.required_experience_years) * 100)

    total_score = (
        required_score * subweights.required_skills
        + experience_score * subweights.experience_fit
        + nice_score * subweights.nice_to_have
    )

    explanation = _combine_explanations(
        [
            f"Required skills match: {resume.required_skills_matched}/{resume.required_skills_total}.",
            f"Experience fit: {resume.experience_years:.1f} yrs vs {resume.required_experience_years:.1f} yrs required.",
            (
                f"Nice-to-have skills match: {resume.nice_to_have_matched}/{resume.nice_to_have_total}."
                if resume.nice_to_have_total > 0
                else "Nice-to-have skills not specified."
            ),
        ]
    )
    return _clamp(total_score), explanation


def _project_originality(projects: List[Dict[str, object]]) -> Tuple[Optional[float], str]:
    if not projects:
        return None, "No GitHub projects available to assess originality."

    project_scores: List[float] = []
    tutorial_flags: List[str] = []
    green_flags: List[str] = []

    for project in projects:
        originality = project.get("originality_score")
        if isinstance(originality, (int, float)):
            project_scores.append(float(originality))
        if project.get("is_tutorial"):
            indicators = project.get("tutorial_indicators") or []
            tutorial_flags.extend([str(item) for item in indicators])
        green = project.get("green_flags") or []
        green_flags.extend([str(item) for item in green])

    if not project_scores:
        return None, "Originality score missing from GitHub analysis."

    average_score = sum(project_scores) / len(project_scores)
    explanation_lines = [f"Average originality across {len(project_scores)} projects: {average_score:.1f}." ]
    if tutorial_flags:
        explanation_lines.append(f"Tutorial indicators: {', '.join(sorted(set(tutorial_flags)))}.")
    if green_flags:
        explanation_lines.append(f"Originality signals: {', '.join(sorted(set(green_flags)))}.")

    return _clamp(average_score), _combine_explanations(explanation_lines)


def _github_component_score(
    github: GitHubAnalysis,
) -> Tuple[float, float, float, List[str]]:
    code_quality = _clamp(github.code_quality_score)
    documentation = _clamp(github.documentation_score)
    engineering = _clamp(github.engineering_practices_score)
    return code_quality, documentation, engineering, [
        f"Code quality score: {code_quality:.1f}.",
        f"Documentation quality score: {documentation:.1f}.",
        f"Engineering practices score: {engineering:.1f}.",
    ]


def compute_score(
    candidate_id: str,
    job_id: str,
    config: ScoringConfig,
    resume: Optional[ResumeAnalysis] = None,
    github: Optional[GitHubAnalysis] = None,
    owner_id: Optional[str] = None,
) -> ScoreResult:
    normalized_config = config.normalized()
    weights = normalized_config.category_weights

    components: List[ScoreComponent] = []
    available_categories: List[str] = []

    if resume:
        resume_score, resume_explanation = _resume_score(resume, normalized_config)
        components.append(
            ScoreComponent(
                category="resume_skills",
                score=resume_score,
                weight=weights.resume_skills,
                weighted_score=0.0,
                explanation=resume_explanation,
            )
        )
        available_categories.append("resume_skills")
    else:
        components.append(
            ScoreComponent(
                category="resume_skills",
                score=None,
                weight=weights.resume_skills,
                weighted_score=0.0,
                explanation="Resume analysis missing; resume/skills score not calculated.",
            )
        )

    if github:
        code_quality, documentation, engineering, explanations = _github_component_score(github)
        originality_score, originality_explanation = _project_originality(github.projects)
        components.extend(
            [
                ScoreComponent(
                    category="github_code_quality",
                    score=code_quality,
                    weight=weights.github_code_quality,
                    weighted_score=0.0,
                    explanation=explanations[0],
                ),
                ScoreComponent(
                    category="documentation_quality",
                    score=documentation,
                    weight=weights.documentation_quality,
                    weighted_score=0.0,
                    explanation=explanations[1],
                ),
                ScoreComponent(
                    category="engineering_practices",
                    score=engineering,
                    weight=weights.engineering_practices,
                    weighted_score=0.0,
                    explanation=explanations[2],
                ),
                ScoreComponent(
                    category="project_originality",
                    score=originality_score,
                    weight=weights.project_originality,
                    weighted_score=0.0,
                    explanation=originality_explanation,
                ),
            ]
        )
        available_categories.extend(
            [
                "github_code_quality",
                "documentation_quality",
                "engineering_practices",
                "project_originality",
            ]
        )
    else:
        components.extend(
            [
                ScoreComponent(
                    category="github_code_quality",
                    score=None,
                    weight=weights.github_code_quality,
                    weighted_score=0.0,
                    explanation="GitHub analysis missing; code quality not scored.",
                ),
                ScoreComponent(
                    category="project_originality",
                    score=None,
                    weight=weights.project_originality,
                    weighted_score=0.0,
                    explanation="GitHub analysis missing; originality not scored.",
                ),
                ScoreComponent(
                    category="documentation_quality",
                    score=None,
                    weight=weights.documentation_quality,
                    weighted_score=0.0,
                    explanation="GitHub analysis missing; documentation not scored.",
                ),
                ScoreComponent(
                    category="engineering_practices",
                    score=None,
                    weight=weights.engineering_practices,
                    weighted_score=0.0,
                    explanation="GitHub analysis missing; engineering practices not scored.",
                ),
            ]
        )

    normalized_weights = _normalize_available(
        {
            "resume_skills": weights.resume_skills,
            "github_code_quality": weights.github_code_quality,
            "project_originality": weights.project_originality,
            "documentation_quality": weights.documentation_quality,
            "engineering_practices": weights.engineering_practices,
        },
        available_categories,
    )

    total_score = 0.0
    for component in components:
        if component.score is None:
            continue
        normalized_weight = normalized_weights.get(component.category, 0.0)
        component.weighted_score = component.score * normalized_weight
        total_score += component.weighted_score

    total_score = _clamp(total_score)

    explanation = _combine_explanations(
        [
            "Candidate scoring summary:",
            *[f"- {component.category.replace('_', ' ').title()}: {component.explanation}" for component in components],
        ]
    )

    return ScoreResult(
        candidate_id=candidate_id,
        job_id=job_id,
        total_score=total_score,
        breakdown=ScoreBreakdown(components=components),
        explanation=explanation,
        owner_id=owner_id,
    )

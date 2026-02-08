from __future__ import annotations

from collections import Counter
from typing import Iterable, List, Optional

from hirerank.dashboard.models import (
    CandidateDashboardEntry,
    JobInsights,
    ScoreDistributionBucket,
    SkillMatchCount,
)
from hirerank.storage.application_repository import ApplicationRepository
from hirerank.storage.scoring_repository import ScoringRepository

_VALID_STATUSES = {"new", "shortlisted", "rejected"}


def _normalize_skill(skill: str) -> str:
    return skill.strip().lower()


def _summarize_explanation(explanation: str, max_lines: int = 2) -> str:
    lines = [line.strip() for line in explanation.splitlines() if line.strip()]
    summary = "\n".join(lines[:max_lines])
    return summary or "Score explanation pending."


def list_candidates_for_job(
    owner_id: str,
    job_id: str,
    applications_repo: ApplicationRepository,
    scoring_repo: ScoringRepository,
    min_score: Optional[float] = None,
    status: Optional[str] = None,
    skills: Optional[Iterable[str]] = None,
) -> List[CandidateDashboardEntry]:
    applications = applications_repo.list_by_job(owner_id=owner_id, job_id=job_id)

    status_filter = status.lower().strip() if status else None
    if status_filter and status_filter not in _VALID_STATUSES:
        raise ValueError(f"Unsupported status '{status}'.")

    skill_filters = {_normalize_skill(skill) for skill in skills or [] if skill.strip()}

    filtered_apps = []
    for application in applications:
        if status_filter and application.status.lower() != status_filter:
            continue
        if skill_filters:
            app_skills = {_normalize_skill(skill) for skill in application.skills}
            if not app_skills.intersection(skill_filters):
                continue
        filtered_apps.append(application)

    scores_by_candidate = scoring_repo.list_by_job(owner_id=owner_id, job_id=job_id)
    entries: List[CandidateDashboardEntry] = []
    for application in filtered_apps:
        score = scores_by_candidate.get(application.candidate_id)
        if min_score is not None:
            if score is None or score.total_score < min_score:
                continue
        entries.append(
            CandidateDashboardEntry(
                application_id=application.application_id,
                candidate_id=application.candidate_id,
                status=application.status,
                skills=application.skills,
                total_score=score.total_score if score else None,
                breakdown=score.breakdown.as_dict() if score else {},
                explanation_summary=_summarize_explanation(score.explanation) if score else "Score pending.",
                explanation=score.explanation if score else "",
                score_created_at=score.created_at.isoformat() if score else None,
            )
        )

    entries.sort(key=lambda entry: (entry.total_score is None, -(entry.total_score or 0.0)))
    return entries


def job_insights(
    owner_id: str,
    job_id: str,
    applications_repo: ApplicationRepository,
    scoring_repo: ScoringRepository,
) -> JobInsights:
    applications = applications_repo.list_by_job(owner_id=owner_id, job_id=job_id)
    scores_by_candidate = scoring_repo.list_by_job(owner_id=owner_id, job_id=job_id)

    scores = [
        scores_by_candidate[application.candidate_id].total_score
        for application in applications
        if application.candidate_id in scores_by_candidate
    ]
    distribution = _score_distribution(scores)

    skill_counter: Counter[str] = Counter()
    display_names = {}
    for application in applications:
        for skill in application.skills:
            normalized = _normalize_skill(skill)
            if not normalized:
                continue
            skill_counter[normalized] += 1
            display_names.setdefault(normalized, skill.strip())

    top_skills = [
        SkillMatchCount(skill=display_names[key], count=count)
        for key, count in skill_counter.most_common(5)
    ]

    return JobInsights(
        job_id=job_id,
        total_applications=len(applications),
        scored_applications=len(scores),
        unscored_applications=len(applications) - len(scores),
        score_distribution=distribution,
        top_skill_matches=top_skills,
    )


def _score_distribution(scores: Iterable[float]) -> List[ScoreDistributionBucket]:
    buckets = [
        (0.0, 20.0, "0-20"),
        (20.0, 40.0, "20-40"),
        (40.0, 60.0, "40-60"),
        (60.0, 80.0, "60-80"),
        (80.0, 100.0, "80-100"),
    ]
    bucket_counts = {label: 0 for _, _, label in buckets}
    for score in scores:
        for min_score, max_score, label in buckets:
            is_last = max_score == 100.0
            if (min_score <= score < max_score) or (is_last and score <= max_score):
                bucket_counts[label] += 1
                break

    return [
        ScoreDistributionBucket(
            label=label,
            min_score=min_score,
            max_score=max_score,
            count=bucket_counts[label],
        )
        for min_score, max_score, label in buckets
    ]

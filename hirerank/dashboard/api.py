from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from hirerank.dashboard.service import job_insights, list_candidates_for_job
from hirerank.storage.application_repository import ApplicationRepository
from hirerank.storage.scoring_repository import ScoringRepository


def _storage_dir() -> Path:
    return Path(os.getenv("HIRERANK_STORAGE_DIR", ".data")).resolve()


def _application_repository() -> ApplicationRepository:
    return ApplicationRepository(_storage_dir() / "applications.json")


def _scoring_repository() -> ScoringRepository:
    return ScoringRepository(_storage_dir() / "scores.json")


def _owner_id(x_owner_id: str = Header(..., alias="X-Owner-Id")) -> str:
    return x_owner_id


app = FastAPI(title="HireRank Dashboard API", version="0.1.0")


@app.get("/dashboard/jobs/{job_id}/candidates")
def dashboard_candidates(
    job_id: str,
    owner_id: str = Depends(_owner_id),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0),
    status: Optional[str] = Query(None, description="new | shortlisted | rejected"),
    skill: Optional[List[str]] = Query(None),
) -> dict:
    try:
        candidates = list_candidates_for_job(
            owner_id=owner_id,
            job_id=job_id,
            applications_repo=_application_repository(),
            scoring_repo=_scoring_repository(),
            min_score=min_score,
            status=status,
            skills=skill,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "job_id": job_id,
        "owner_id": owner_id,
        "candidates": [candidate.__dict__ for candidate in candidates],
    }


@app.get("/dashboard/jobs/{job_id}/insights")
def dashboard_insights(job_id: str, owner_id: str = Depends(_owner_id)) -> dict:
    insights = job_insights(
        owner_id=owner_id,
        job_id=job_id,
        applications_repo=_application_repository(),
        scoring_repo=_scoring_repository(),
    )
    return {
        "job_id": job_id,
        "owner_id": owner_id,
        "insights": {
            "total_applications": insights.total_applications,
            "scored_applications": insights.scored_applications,
            "unscored_applications": insights.unscored_applications,
            "score_distribution": [bucket.__dict__ for bucket in insights.score_distribution],
            "top_skill_matches": [skill.__dict__ for skill in insights.top_skill_matches],
        },
    }

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile

from hirerank.dashboard.service import job_insights, list_candidates_for_job
from hirerank.imports.models import CandidateImportJob
from hirerank.imports.service import (
    enqueue_import,
    parse_csv_preview,
    parse_csv_rows,
    parse_mapping,
    validate_mapping,
)
from hirerank.storage.application_repository import ApplicationRepository
from hirerank.storage.import_repository import CandidateImportRepository
from hirerank.storage.scoring_repository import ScoringRepository
from hirerank.background_jobs.scoring import build_default_coordinator


def _storage_dir() -> Path:
    return Path(os.getenv("HIRERANK_STORAGE_DIR", ".data")).resolve()


def _application_repository() -> ApplicationRepository:
    return ApplicationRepository(_storage_dir() / "applications.json")


def _scoring_repository() -> ScoringRepository:
    return ScoringRepository(_storage_dir() / "scores.json")


def _import_repository() -> CandidateImportRepository:
    return CandidateImportRepository(_storage_dir() / "candidate_imports.json")


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


@app.post("/dashboard/jobs/{job_id}/imports/preview")
def import_preview(
    job_id: str,
    owner_id: str = Depends(_owner_id),
    preview_rows: int = Query(5, ge=1, le=50),
    file: UploadFile = File(...),
) -> dict:
    data = file.file.read()
    preview = parse_csv_preview(data, preview_rows=preview_rows)
    return {
        "job_id": job_id,
        "owner_id": owner_id,
        "headers": preview.headers,
        "rows": preview.rows,
    }


@app.post("/dashboard/jobs/{job_id}/imports")
def create_import_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    owner_id: str = Depends(_owner_id),
    file: UploadFile = File(...),
    mapping: str = Form(...),
) -> dict:
    data = file.file.read()
    headers, rows = parse_csv_rows(data)
    try:
        parsed_mapping = parse_mapping(mapping)
        resolved_mapping = validate_mapping(parsed_mapping, headers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    import_job = CandidateImportJob(
        import_id=str(uuid4()),
        owner_id=owner_id,
        job_id=job_id,
        status="queued",
        headers=headers,
        mapping=resolved_mapping,
        total_rows=len(rows),
        processed_rows=0,
        success_count=0,
        failure_count=0,
        results=[],
    )
    import_repo = _import_repository()
    import_repo.create(import_job)

    background_tasks.add_task(
        enqueue_import,
        import_job,
        import_repo,
        rows,
        _application_repository(),
        build_default_coordinator(_storage_dir()),
    )
    return _serialize_import_job(import_job)


@app.get("/dashboard/jobs/{job_id}/imports/{import_id}")
def get_import_job(
    job_id: str,
    import_id: str,
    owner_id: str = Depends(_owner_id),
) -> dict:
    import_job = _import_repository().get(owner_id=owner_id, job_id=job_id, import_id=import_id)
    if not import_job:
        raise HTTPException(status_code=404, detail="Import job not found.")
    return _serialize_import_job(import_job)


def _serialize_import_job(job: CandidateImportJob) -> dict:
    payload = asdict(job)
    payload["created_at"] = job.created_at.isoformat()
    payload["updated_at"] = job.updated_at.isoformat()
    return payload

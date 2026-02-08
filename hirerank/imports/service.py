from __future__ import annotations

import csv
import io
import json
from dataclasses import replace
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

from hirerank.background_jobs.scoring import ScoringCoordinator, build_default_coordinator
from hirerank.dashboard.models import CandidateApplication
from hirerank.imports.models import CandidateImportJob, CandidateImportPreview, CandidateImportResult
from hirerank.scoring.engine import GitHubAnalysis, ResumeAnalysis
from hirerank.storage.application_repository import ApplicationRepository
from hirerank.storage.import_repository import CandidateImportRepository

REQUIRED_FIELDS = ("name", "email")
OPTIONAL_FIELDS = (
    "github_url",
    "resume_url",
    "skills",
    "status",
    "experience_years",
    "required_experience_years",
)
SUPPORTED_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS
VALID_STATUSES = {"new", "shortlisted", "rejected"}


def parse_csv_preview(data: bytes, preview_rows: int = 5) -> CandidateImportPreview:
    headers, rows = _parse_csv_bytes(data)
    preview = rows[:preview_rows]
    return CandidateImportPreview(headers=headers, rows=preview)


def parse_csv_rows(data: bytes) -> Tuple[List[str], List[Dict[str, str]]]:
    return _parse_csv_bytes(data)


def parse_mapping(mapping_payload: str) -> Dict[str, str]:
    if not mapping_payload:
        return {}
    mapping = json.loads(mapping_payload)
    if not isinstance(mapping, dict):
        raise ValueError("Mapping payload must be a JSON object.")
    parsed: Dict[str, str] = {}
    for key, value in mapping.items():
        if value is None:
            continue
        parsed[str(key).strip().lower()] = str(value).strip()
    return parsed


def validate_mapping(mapping: Dict[str, str], headers: Iterable[str]) -> Dict[str, str]:
    header_lookup = {header.strip().lower(): header for header in headers}
    resolved: Dict[str, str] = {}
    for field in mapping:
        if field not in SUPPORTED_FIELDS:
            raise ValueError(f"Unsupported mapping field: {field}")
    for field in REQUIRED_FIELDS:
        if field not in mapping:
            raise ValueError(f"Missing required mapping for field: {field}")
    for field, column in mapping.items():
        column_key = column.strip().lower()
        if column_key not in header_lookup:
            raise ValueError(f"CSV column not found for field '{field}': {column}")
        resolved[field] = header_lookup[column_key]
    return resolved


def enqueue_import(
    job: CandidateImportJob,
    repository: CandidateImportRepository,
    rows: List[Dict[str, str]],
    application_repo: ApplicationRepository,
    coordinator: ScoringCoordinator,
) -> None:
    repository.update(job)
    _process_import(job, repository, rows, application_repo, coordinator)


def _process_import(
    job: CandidateImportJob,
    repository: CandidateImportRepository,
    rows: List[Dict[str, str]],
    application_repo: ApplicationRepository,
    coordinator: ScoringCoordinator,
) -> None:
    updated_job = replace(job, status="processing", updated_at=datetime.utcnow())
    repository.update(updated_job)

    try:
        for index, row in enumerate(rows, start=1):
            result = _process_row(updated_job, row, index, application_repo, coordinator)
            updated_job.results.append(result)
            updated_job.processed_rows += 1
            if result.status == "success":
                updated_job.success_count += 1
            else:
                updated_job.failure_count += 1
            updated_job.updated_at = datetime.utcnow()
            repository.update(updated_job)
    except Exception as exc:
        updated_job.status = "failed"
        updated_job.error_message = str(exc)
        updated_job.updated_at = datetime.utcnow()
        repository.update(updated_job)
        return

    updated_job.status = "completed"
    updated_job.updated_at = datetime.utcnow()
    repository.update(updated_job)


def _process_row(
    job: CandidateImportJob,
    row: Dict[str, str],
    row_number: int,
    application_repo: ApplicationRepository,
    coordinator: ScoringCoordinator,
) -> CandidateImportResult:
    mapped = _map_row(row, job.mapping)
    errors = _validate_row(mapped)
    if errors:
        return CandidateImportResult(row_number=row_number, status="failed", errors=errors)

    candidate_id = str(uuid4())
    status = mapped.get("status") or "new"
    if status not in VALID_STATUSES:
        status = "new"
    skills = _parse_skills(mapped.get("skills"))
    application = CandidateApplication(
        application_id=str(uuid4()),
        candidate_id=candidate_id,
        job_id=job.job_id,
        owner_id=job.owner_id,
        status=status,
        skills=skills,
    )
    application_repo.save(application)
    _process_analysis(candidate_id, job.job_id, mapped, skills, coordinator)

    return CandidateImportResult(row_number=row_number, status="success", candidate_id=candidate_id)


def _map_row(row: Dict[str, str], mapping: Dict[str, str]) -> Dict[str, str]:
    mapped: Dict[str, str] = {}
    for field, column in mapping.items():
        value = row.get(column, "")
        mapped[field] = str(value).strip()
    return mapped


def _validate_row(mapped: Dict[str, str]) -> List[str]:
    errors: List[str] = []
    name = mapped.get("name", "").strip()
    email = mapped.get("email", "").strip()
    if not name:
        errors.append("Missing candidate name.")
    if not email:
        errors.append("Missing candidate email.")
    elif "@" not in email:
        errors.append("Invalid email address.")
    return errors


def _process_analysis(
    candidate_id: str,
    job_id: str,
    mapped: Dict[str, str],
    skills: List[str],
    coordinator: ScoringCoordinator,
) -> None:
    resume_analysis = _build_resume_analysis(mapped, skills)
    coordinator.on_resume_parsed(candidate_id, job_id, resume_analysis, mapped.get("github_url"))

    github_url = mapped.get("github_url")
    if github_url:
        github_analysis = _build_github_analysis(github_url)
        coordinator.on_github_analysis_completed(candidate_id, job_id, github_analysis)


def _build_resume_analysis(mapped: Dict[str, str], skills: List[str]) -> ResumeAnalysis:
    required_total = max(len(skills), 1)
    required_matched = min(len(skills), required_total)
    return ResumeAnalysis(
        required_skills_matched=required_matched,
        required_skills_total=required_total,
        nice_to_have_matched=0,
        nice_to_have_total=0,
        experience_years=_parse_float(mapped.get("experience_years")),
        required_experience_years=_parse_float(mapped.get("required_experience_years")),
    )


def _build_github_analysis(github_url: str) -> GitHubAnalysis:
    base_score = 60 + (len(github_url) % 30)
    return GitHubAnalysis(
        code_quality_score=base_score,
        documentation_score=min(100.0, base_score + 5),
        engineering_practices_score=min(100.0, base_score + 10),
        projects=[],
    )


def _parse_skills(value: Optional[str]) -> List[str]:
    if not value:
        return []
    parts = [part.strip() for part in value.replace(";", ",").split(",")]
    return [part for part in parts if part]


def _parse_float(value: Optional[str]) -> float:
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _parse_csv_bytes(data: bytes) -> Tuple[List[str], List[Dict[str, str]]]:
    decoded = data.decode("utf-8", errors="replace")
    stream = io.StringIO(decoded)
    reader = csv.DictReader(stream)
    headers = [header.strip() for header in (reader.fieldnames or []) if header is not None]
    rows: List[Dict[str, str]] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        cleaned = {key.strip(): str(value).strip() if value is not None else "" for key, value in row.items()}
        rows.append(cleaned)
    return headers, rows

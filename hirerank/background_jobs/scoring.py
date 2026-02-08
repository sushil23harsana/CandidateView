from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from hirerank.scoring.config import ScoringConfig
from hirerank.scoring.engine import GitHubAnalysis, ResumeAnalysis, compute_score
from hirerank.scoring.models import ScoreResult
from hirerank.storage.scoring_config_repository import ScoringConfigRepository
from hirerank.storage.scoring_repository import ScoringRepository


@dataclass
class CandidateAnalysisState:
    candidate_id: str
    job_id: str
    resume_analysis: Optional[ResumeAnalysis] = None
    github_analysis: Optional[GitHubAnalysis] = None
    github_url: Optional[str] = None

    def ready_for_scoring(self, github_required: bool) -> bool:
        if self.resume_analysis is None:
            return False
        if self.github_analysis is not None:
            return True
        if github_required:
            return False
        return not self.github_url


@dataclass
class AnalysisStateStore:
    _state: Dict[str, CandidateAnalysisState] = field(default_factory=dict)

    def get_or_create(self, candidate_id: str, job_id: str) -> CandidateAnalysisState:
        key = f"{job_id}:{candidate_id}"
        if key not in self._state:
            self._state[key] = CandidateAnalysisState(candidate_id=candidate_id, job_id=job_id)
        return self._state[key]


class ScoringCoordinator:
    def __init__(
        self,
        config_repo: ScoringConfigRepository,
        result_repo: ScoringRepository,
        state_store: Optional[AnalysisStateStore] = None,
    ) -> None:
        self.config_repo = config_repo
        self.result_repo = result_repo
        self.state_store = state_store or AnalysisStateStore()

    def on_resume_parsed(
        self,
        candidate_id: str,
        job_id: str,
        resume_analysis: ResumeAnalysis,
        github_url: Optional[str],
    ) -> Optional[ScoreResult]:
        state = self.state_store.get_or_create(candidate_id, job_id)
        state.resume_analysis = resume_analysis
        state.github_url = github_url
        return self._maybe_score(state)

    def on_github_analysis_completed(
        self,
        candidate_id: str,
        job_id: str,
        github_analysis: GitHubAnalysis,
    ) -> Optional[ScoreResult]:
        state = self.state_store.get_or_create(candidate_id, job_id)
        state.github_analysis = github_analysis
        return self._maybe_score(state)

    def _maybe_score(self, state: CandidateAnalysisState) -> Optional[ScoreResult]:
        config = self.config_repo.get(state.job_id)
        if not state.ready_for_scoring(config.github_required):
            return None

        result = compute_score(
            candidate_id=state.candidate_id,
            job_id=state.job_id,
            config=config,
            resume=state.resume_analysis,
            github=state.github_analysis,
        )
        self.result_repo.save(result)
        return result


def build_default_coordinator(storage_root: Path) -> ScoringCoordinator:
    config_repo = ScoringConfigRepository(storage_root / "scoring_configs.json")
    result_repo = ScoringRepository(storage_root / "scoring_results.json")
    return ScoringCoordinator(config_repo=config_repo, result_repo=result_repo)

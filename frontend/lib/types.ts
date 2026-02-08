export interface JobSummary {
  id: string;
  title: string;
  location: string;
  status: string;
  totalApplications: number;
  updatedAt: string;
}

export interface CandidateScore {
  application_id: string;
  candidate_id: string;
  status: string;
  skills: string[];
  total_score: number;
  explanation_summary: string;
  score_created_at: string;
}

export interface CandidatesResponse {
  job_id: string;
  owner_id: string;
  candidates: CandidateScore[];
}

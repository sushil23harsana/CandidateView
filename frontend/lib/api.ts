import { CandidatesResponse, JobSummary } from "@/lib/types";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

function buildHeaders(ownerId: string) {
  return {
    "Content-Type": "application/json",
    "X-Owner-Id": ownerId
  };
}

export async function fetchJobs(ownerId: string): Promise<JobSummary[]> {
  const response = await fetch(`${API_BASE_URL}/dashboard/jobs`, {
    headers: buildHeaders(ownerId),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Failed to load jobs");
  }

  const data = (await response.json()) as { jobs: JobSummary[] };
  return data.jobs ?? [];
}

export async function fetchCandidates(
  ownerId: string,
  jobId: string
): Promise<CandidatesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/jobs/${jobId}/candidates`,
    {
      headers: buildHeaders(ownerId),
      cache: "no-store"
    }
  );

  if (!response.ok) {
    throw new Error("Failed to load candidates");
  }

  return (await response.json()) as CandidatesResponse;
}

export const fallbackJobs: JobSummary[] = [
  {
    id: "job_456",
    title: "Senior Python Developer",
    location: "Remote",
    status: "Active",
    totalApplications: 120,
    updatedAt: "2024-08-12T10:30:00Z"
  },
  {
    id: "job_789",
    title: "Frontend Engineer",
    location: "Bangalore",
    status: "Paused",
    totalApplications: 78,
    updatedAt: "2024-08-10T16:15:00Z"
  }
];

export const fallbackCandidates: CandidatesResponse = {
  job_id: "job_456",
  owner_id: "owner_demo",
  candidates: [
    {
      application_id: "app_001",
      candidate_id: "cand_001",
      status: "shortlisted",
      skills: ["Python", "FastAPI", "PostgreSQL"],
      total_score: 91.2,
      explanation_summary: "Required skills match: 5/5.",
      score_created_at: "2024-08-01T12:34:56Z"
    },
    {
      application_id: "app_002",
      candidate_id: "cand_002",
      status: "review",
      skills: ["Python", "Django", "AWS"],
      total_score: 84.7,
      explanation_summary: "Strong backend skills with cloud experience.",
      score_created_at: "2024-08-02T09:20:00Z"
    },
    {
      application_id: "app_003",
      candidate_id: "cand_003",
      status: "waitlist",
      skills: ["Python", "Flask", "Redis"],
      total_score: 77.9,
      explanation_summary: "Meets core requirements with smaller projects.",
      score_created_at: "2024-08-03T15:05:00Z"
    }
  ]
};

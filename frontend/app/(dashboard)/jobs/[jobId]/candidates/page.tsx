import Link from "next/link";
import { getServerSession } from "next-auth";
import { ArrowLeft, Info } from "lucide-react";

import { authOptions } from "@/lib/auth";
import { fetchCandidates, fallbackCandidates } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";

interface CandidatesPageProps {
  params: { jobId: string };
}

export default async function CandidatesPage({ params }: CandidatesPageProps) {
  const session = await getServerSession(authOptions);
  const ownerId = session?.user?.id ?? session?.user?.email ?? "owner_demo";

  let data = fallbackCandidates;
  let usingFallback = false;

  try {
    data = await fetchCandidates(ownerId, params.jobId);
  } catch {
    usingFallback = true;
    data = { ...fallbackCandidates, job_id: params.jobId };
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link href="/jobs" className="text-sm text-muted-foreground">
            <ArrowLeft className="mr-2 inline h-4 w-4" />
            Back to jobs
          </Link>
          <h2 className="mt-2 text-2xl font-semibold">Ranked candidates</h2>
          <p className="text-sm text-muted-foreground">
            Job ID: {data.job_id}
          </p>
        </div>
        <Badge variant="outline">Read-only</Badge>
      </div>

      {usingFallback && (
        <Card className="border-dashed">
          <CardHeader>
            <CardTitle>Demo data</CardTitle>
            <CardDescription>
              Backend API is unavailable. Showing sample candidate rankings to
              verify the table layout.
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Candidate ranking table</CardTitle>
          <CardDescription>
            Scores are weighted by job requirements and refreshed when new
            applications are analyzed.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Candidate</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Skills</TableHead>
                <TableHead>Total score</TableHead>
                <TableHead>Last scored</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.candidates.map((candidate) => (
                <TableRow key={candidate.application_id}>
                  <TableCell>
                    <div>
                      <p className="font-medium">{candidate.candidate_id}</p>
                      <p className="text-xs text-muted-foreground">
                        {candidate.application_id}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{candidate.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-2">
                      {candidate.skills.map((skill) => (
                        <Badge key={skill}>{skill}</Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="text-lg font-semibold">
                        {candidate.total_score.toFixed(1)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {candidate.explanation_summary}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    {new Date(candidate.score_created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="mt-4 flex items-start gap-2 rounded-md border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
            <Info className="mt-0.5 h-4 w-4" />
            Decisions and status changes are disabled in this read-only phase.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

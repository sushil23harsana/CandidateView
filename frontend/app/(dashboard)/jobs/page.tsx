import Link from "next/link";
import { getServerSession } from "next-auth";
import { Calendar, ChevronRight, MapPin } from "lucide-react";

import { authOptions } from "@/lib/auth";
import { fetchJobs, fallbackJobs } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default async function JobsPage() {
  const session = await getServerSession(authOptions);
  const ownerId = session?.user?.id ?? session?.user?.email ?? "owner_demo";

  let jobs = fallbackJobs;
  let usingFallback = false;

  try {
    jobs = await fetchJobs(ownerId);
  } catch {
    usingFallback = true;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Open roles</h2>
          <p className="text-sm text-muted-foreground">
            Review job pipelines and jump into ranked candidates.
          </p>
        </div>
        <Badge variant="outline">Read-only</Badge>
      </div>
      {usingFallback && (
        <Card className="border-dashed">
          <CardHeader>
            <CardTitle>Demo data</CardTitle>
            <CardDescription>
              Backend API is unavailable. Showing sample jobs to help validate the
              dashboard layout.
            </CardDescription>
          </CardHeader>
        </Card>
      )}
      <div className="grid gap-4 lg:grid-cols-2">
        {jobs.map((job) => (
          <Card key={job.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{job.title}</CardTitle>
                <Badge>{job.status}</Badge>
              </div>
              <CardDescription>
                {job.totalApplications} applications · Updated{" "}
                {new Date(job.updatedAt).toLocaleDateString()}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4" />
                {job.location}
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                Job ID: {job.id}
              </div>
              <Link
                href={`/jobs/${job.id}/candidates`}
                className="inline-flex items-center text-sm font-medium text-primary"
              >
                View ranked candidates
                <ChevronRight className="ml-1 h-4 w-4" />
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

import { getServerSession } from "next-auth";

import { authOptions } from "@/lib/auth";
import { fetchJobs, fallbackJobs } from "@/lib/api";
import { ImportCsv } from "@/components/imports/import-csv";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default async function ImportsPage() {
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
      {usingFallback && (
        <Card className="border-dashed">
          <CardHeader className="flex flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>Demo mode</CardTitle>
              <CardDescription>
                Backend API is unavailable. Preview and import actions will fail,
                but you can review the CSV import flow.
              </CardDescription>
            </div>
            <Badge variant="outline">Offline</Badge>
          </CardHeader>
        </Card>
      )}
      <ImportCsv ownerId={ownerId} jobs={jobs} />
    </div>
  );
}

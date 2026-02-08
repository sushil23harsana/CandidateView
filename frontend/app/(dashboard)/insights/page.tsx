import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function InsightsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Job insights</h2>
          <p className="text-sm text-muted-foreground">
            Coming soon: distribution charts and top skill matches.
          </p>
        </div>
        <Badge variant="outline">Read-only</Badge>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Insights placeholder</CardTitle>
          <CardDescription>
            Insights API integration will surface application counts, score
            distribution, and skill trends.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Connect the backend /dashboard/jobs/{"{job_id}"}/insights endpoint to
            visualize the ranking pipeline metrics.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
